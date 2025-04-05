#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Email Processing System for Email Intelligence
This module processes emails to extract structure, content, and metadata.
"""

import re
import uuid
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from email import message_from_string
from email.utils import parseaddr, getaddresses
from email.header import decode_header
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict
from pathlib import Path
from email.parser import Parser
from email.policy import default
from html.parser import HTMLParser
from datetime import datetime

from ml.config import get_email_config
from ml.models.model_loader import email_categorization_model, sentiment_model
from ml.storage import email_storage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EmailAttachment:
    """Represents an email attachment."""
    filename: str
    content_type: str
    size: int
    content_id: Optional[str] = None
    data: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding binary data)."""
        result = asdict(self)
        # Don't include binary data in dictionary representation
        if 'data' in result:
            result['data'] = f"<binary data: {self.size} bytes>"
        return result


@dataclass
class EmailAddress:
    """Represents an email address with name and address parts."""
    name: str
    address: str
    
    @classmethod
    def from_string(cls, address_string: str) -> 'EmailAddress':
        """Create EmailAddress from string like 'Name <email@example.com>'."""
        name, address = parseaddr(address_string)
        # Decode name if needed
        try:
            decoded_parts = []
            for part, encoding in decode_header(name):
                if isinstance(part, bytes):
                    decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
                else:
                    decoded_parts.append(part)
            name = ''.join(decoded_parts)
        except Exception as e:
            logger.warning(f"Failed to decode header: {e}")
        
        return cls(name=name, address=address)


@dataclass
class EmailMetadata:
    """Contains metadata about an email."""
    message_id: str
    subject: str
    from_address: EmailAddress
    to_addresses: List[EmailAddress]
    cc_addresses: List[EmailAddress] = field(default_factory=list)
    bcc_addresses: List[EmailAddress] = field(default_factory=list)
    reply_to_addresses: List[EmailAddress] = field(default_factory=list)
    date: Optional[datetime] = None
    in_reply_to: Optional[str] = None
    references: List[str] = field(default_factory=list)
    thread_id: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "message_id": self.message_id,
            "subject": self.subject,
            "from": asdict(self.from_address),
            "to": [asdict(addr) for addr in self.to_addresses],
            "cc": [asdict(addr) for addr in self.cc_addresses],
            "bcc": [asdict(addr) for addr in self.bcc_addresses],
            "reply_to": [asdict(addr) for addr in self.reply_to_addresses],
            "date": self.date.isoformat() if self.date else None,
            "in_reply_to": self.in_reply_to,
            "references": self.references,
            "thread_id": self.thread_id,
            "headers": self.headers
        }
        return result


@dataclass
class EmailContent:
    """Contains the content of an email."""
    text_plain: str = ""
    text_html: str = ""
    extracted_text: str = ""  # Text extracted from HTML
    urls: List[str] = field(default_factory=list)
    attachments: List[EmailAttachment] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text_plain": self.text_plain,
            "text_html": self.text_html[:100] + "..." if len(self.text_html) > 100 else self.text_html,  # Truncate HTML
            "extracted_text": self.extracted_text,
            "urls": self.urls,
            "attachments": [attachment.to_dict() for attachment in self.attachments]
        }
    
    def get_best_text(self) -> str:
        """Return the best text representation of the email content."""
        if self.extracted_text:
            return self.extracted_text
        if self.text_plain:
            return self.text_plain
        return "No text content available"


@dataclass
class ProcessedEmail:
    """Represents a processed email with metadata and content."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: EmailMetadata = None
    content: EmailContent = None
    category: str = "unclassified"
    priority: int = 3  # 1 (highest) to 5 (lowest)
    is_new_thread: bool = True
    is_auto_reply: bool = False
    client_id: Optional[str] = None
    processed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "content": self.content.to_dict() if self.content else None,
            "category": self.category,
            "priority": self.priority,
            "is_new_thread": self.is_new_thread,
            "is_auto_reply": self.is_auto_reply,
            "client_id": self.client_id,
            "processed_at": self.processed_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class HTMLTextExtractor(HTMLParser):
    """HTML parser to extract text content from HTML emails."""
    
    def __init__(self):
        """Initialize HTML parser."""
        super().__init__()
        self.result = []
        self.skip = False
    
    def handle_starttag(self, tag, attrs):
        """Handle start tags, skip script and style content."""
        if tag in ("script", "style"):
            self.skip = True
    
    def handle_endtag(self, tag):
        """Handle end tags, resume processing after script/style."""
        if tag in ("script", "style"):
            self.skip = False
    
    def handle_data(self, data):
        """Process text data if not in skip mode."""
        if not self.skip and data.strip():
            self.result.append(data.strip())
    
    def get_text(self) -> str:
        """
        Get extracted text content.
        
        Returns:
            Concatenated text content
        """
        return ' '.join(self.result)


class EmailProcessor:
    """
    Email processing system that extracts intelligence from emails.
    """
    
    def __init__(self):
        """Initialize email processor."""
        self.parser = Parser(policy=default)
        logger.info("Email processor initialized")
    
    def process_email(self, email_raw: str) -> Dict[str, Any]:
        """
        Process an email message.
        
        Args:
            email_raw: Raw email content (RFC 5322 format)
            
        Returns:
            Dictionary with processing results
        """
        # Create an email ID
        email_id = str(uuid.uuid4())
        processed_time = datetime.now().isoformat()
        
        try:
            # Parse email
            parsed_email = self.parser.parsestr(email_raw)
            
            # Extract metadata
            metadata = self._extract_metadata(parsed_email)
            
            # Extract content
            text_content, html_content = self._extract_content(parsed_email)
            
            # Get email subject
            subject = metadata.get('subject', '')
            
            # Process attachments if any
            attachments = self._extract_attachments(parsed_email)
            
            # Extract URLs if HTML content exists
            urls = self._extract_urls(html_content) if html_content else []
            
            # Perform content analysis
            content_analysis = self._analyze_content(subject, text_content)
            
            # Determine if this is an auto-reply
            is_auto_reply = self._detect_auto_reply(subject, text_content, metadata)
            
            # Calculate email priority
            priority = self._calculate_priority(metadata, content_analysis, is_auto_reply)
            
            # Results dictionary
            results = {
                "id": email_id,
                "processed_at": processed_time,
                "metadata": metadata,
                "content": {
                    "text": text_content,
                    "html": html_content is not None,
                    "html_preview": html_content[:200] if html_content else None,
                    "attachment_count": len(attachments),
                    "attachments": attachments,
                    "urls": urls
                },
                "analysis": content_analysis,
                "is_auto_reply": is_auto_reply,
                "priority": priority
            }
            
            # Store email in database
            self._store_email(email_id, results)
            
            logger.info(f"Email processed successfully: {email_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return {
                "id": email_id,
                "processed_at": processed_time,
                "error": str(e),
                "status": "failed"
            }
    
    def _extract_metadata(self, email) -> Dict[str, Any]:
        """
        Extract metadata from an email.
        
        Args:
            email: Parsed email object
            
        Returns:
            Dictionary with email metadata
        """
        metadata = {
            "subject": email.get("Subject", ""),
            "from": email.get("From", ""),
            "to": email.get("To", ""),
            "cc": email.get("Cc", ""),
            "date": email.get("Date", ""),
            "message_id": email.get("Message-ID", ""),
            "in_reply_to": email.get("In-Reply-To", ""),
            "references": email.get("References", "")
        }
        
        # Extract email domain for analytics
        from_email = metadata["from"]
        domain_match = re.search(r'@([\w.-]+)', from_email)
        if domain_match:
            metadata["sender_domain"] = domain_match.group(1)
        
        return metadata
    
    def _extract_content(self, email) -> Tuple[str, Optional[str]]:
        """
        Extract text and HTML content from an email.
        
        Args:
            email: Parsed email object
            
        Returns:
            Tuple of (text_content, html_content)
        """
        text_content = None
        html_content = None
        
        # Process each part in the email
        if email.is_multipart():
            for part in email.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    text_content = part.get_payload(decode=True).decode(errors='replace')
                elif content_type == "text/html":
                    html_content = part.get_payload(decode=True).decode(errors='replace')
        else:
            # Single part email
            content_type = email.get_content_type()
            if content_type == "text/plain":
                text_content = email.get_payload(decode=True).decode(errors='replace')
            elif content_type == "text/html":
                html_content = email.get_payload(decode=True).decode(errors='replace')
        
        # If we have HTML but no text, extract text from HTML
        if html_content and not text_content:
            try:
                # Try BeautifulSoup first
                soup = BeautifulSoup(html_content, 'html.parser')
                text_content = soup.get_text(separator=' ', strip=True)
            except:
                # Fall back to simpler parser
                extractor = HTMLTextExtractor()
                extractor.feed(html_content)
                text_content = extractor.get_text()
        
        # Ensure text content is not None
        if not text_content:
            text_content = ""
            
        return text_content, html_content
    
    def _extract_attachments(self, email) -> List[Dict[str, Any]]:
        """
        Extract attachments from an email.
        
        Args:
            email: Parsed email object
            
        Returns:
            List of dictionaries with attachment information
        """
        attachments = []
        
        if email.is_multipart():
            for part in email.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        # Don't store actual attachment content - just metadata
                        attachments.append({
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True))
                        })
        
        return attachments
    
    def _extract_urls(self, html_content: str) -> List[str]:
        """
        Extract URLs from HTML content.
        
        Args:
            html_content: HTML content of the email
            
        Returns:
            List of URLs found in the HTML
        """
        if not html_content:
            return []
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            urls = []
            
            # Extract links
            for link in soup.find_all('a', href=True):
                url = link['href']
                if url.startswith(('http://', 'https://')):
                    urls.append(url)
                    
            return urls
        except Exception as e:
            logger.error(f"Error extracting URLs: {e}")
            return []
    
    def _analyze_content(self, subject: str, text_content: str) -> Dict[str, Any]:
        """
        Analyze the content of an email.
        
        Args:
            subject: Email subject
            text_content: Text content of the email
            
        Returns:
            Dictionary with analysis results
        """
        # Initialize analysis dictionary
        analysis = {}
        
        # Categorize email
        categorization = email_categorization_model.categorize_email(subject, text_content)
        analysis["categorization"] = categorization
        
        # Analyze sentiment
        sentiment_results = sentiment_model.analyze_sentiment(text_content)
        analysis["sentiment"] = sentiment_results
        
        # Extract key phrases (simplified - would use NLP model in production)
        words = text_content.split()
        analysis["word_count"] = len(words)
        analysis["character_count"] = len(text_content)
        
        # Identify potential keywords
        common_words = {"the", "and", "to", "of", "a", "in", "for", "is", "on", "that", "by", "this", "with", "you", "it"}
        words_lower = [word.lower() for word in words if len(word) > 3]
        word_freq = {}
        for word in words_lower:
            if word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
                
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        analysis["keywords"] = [{"word": word, "count": count} for word, count in keywords]
        
        # Check for urgency words
        urgency_words = {"urgent", "asap", "immediately", "emergency", "critical", "important"}
        has_urgency = any(word.lower() in urgency_words for word in words)
        analysis["urgent"] = has_urgency
        
        return analysis
    
    def _detect_auto_reply(self, subject: str, text_content: str, metadata: Dict[str, Any]) -> bool:
        """
        Detect if email is an auto-reply.
        
        Args:
            subject: Email subject
            text_content: Email text content
            metadata: Email metadata
            
        Returns:
            True if email appears to be an auto-reply
        """
        # Common auto-reply headers
        auto_reply_headers = [
            'Auto-Submitted', 'X-Autoreply', 'X-Auto-Response-Suppress', 
            'X-AutoReply-From', 'Precedence', 'X-Autorespond'
        ]
        
        # Check for auto-reply headers
        for header in auto_reply_headers:
            if header in metadata:
                return True
        
        # Check subject for common auto-reply phrases
        auto_reply_subjects = [
            'auto', 'automatic', 'out of office', 'away', 'vacation', 
            'ooo', 'on leave', 'auto-reply', 'autoreply'
        ]
        subject_lower = subject.lower()
        if any(phrase in subject_lower for phrase in auto_reply_subjects):
            return True
        
        # Check content for common auto-reply phrases
        content_lower = text_content.lower()
        auto_reply_phrases = [
            'automatic response', 'out of office', 'not in the office',
            'on vacation', 'auto-generated', 'auto reply', 'autoresponder',
            'automatic reply', 'do not reply', 'will be away', 'this is an automated email'
        ]
        if any(phrase in content_lower for phrase in auto_reply_phrases):
            return True
            
        return False
    
    def _calculate_priority(self, metadata: Dict[str, Any], analysis: Dict[str, Any], is_auto_reply: bool) -> Dict[str, Any]:
        """
        Calculate email priority based on various factors.
        
        Args:
            metadata: Email metadata
            analysis: Content analysis results
            is_auto_reply: Whether email is an auto-reply
            
        Returns:
            Dictionary with priority information
        """
        # Default priority is normal
        priority_score = 5  # Scale of 1-10
        priority_level = "normal"
        factors = []
        
        # Auto-replies are low priority
        if is_auto_reply:
            priority_score = 1
            priority_level = "low"
            factors.append("auto-reply")
        else:
            # Check sentiment
            sentiment = analysis.get("sentiment", {}).get("overall")
            if sentiment == "negative":
                priority_score += 2
                factors.append("negative sentiment")
            
            # Check urgency words
            if analysis.get("urgent", False):
                priority_score += 3
                factors.append("urgent keywords")
            
            # Check categorization
            categorization = analysis.get("categorization", {})
            if categorization and categorization.get("enabled", False):
                primary_category = categorization.get("primary_category")
                if primary_category == "complaint":
                    priority_score += 2
                    factors.append("complaint")
                elif primary_category == "support":
                    priority_score += 1
                    factors.append("support request")
                elif primary_category == "sales":
                    priority_score += 1
                    factors.append("sales inquiry")
            
            # Determine priority level
            if priority_score >= 8:
                priority_level = "high"
            elif priority_score >= 5:
                priority_level = "normal"
            else:
                priority_level = "low"
        
        return {
            "level": priority_level,
            "score": priority_score,
            "factors": factors
        }
    
    def _store_email(self, email_id: str, email_data: Dict[str, Any]) -> bool:
        """
        Store processed email in storage.
        
        Args:
            email_id: Email ID
            email_data: Processed email data
            
        Returns:
            True if successful, False otherwise
        """
        if email_storage is not None:
            return email_storage.save_email(email_data)
        else:
            logger.warning("Email storage not available, email not saved")
            return False


# Example usage
if __name__ == "__main__":
    # Create email processor
    processor = EmailProcessor()
    
    # Sample email for testing
    sample_email = """From: "John Doe" <john.doe@example.com>
To: "Support Team" <support@guardsrobbers.com>
Subject: Need urgent help with ARP Guard setup
Date: Thu, 15 Jun 2023 10:30:15 -0700
Content-Type: text/plain

Hello Support Team,

I'm having trouble setting up the ARP Guard on our network. The installation 
went fine, but now I'm seeing error messages when trying to configure the 
detection rules.

The error says "Invalid network segment format" but I've double-checked 
my network configuration and everything seems correct.

This is quite urgent as we need to have security monitoring in place before 
the end of the week.

Thank you for your help!

John Doe
Network Administrator
Example Corp.
"""
    
    # Process email
    result = processor.process_email(sample_email)
    
    # Print results
    print("\nEmail Processing Results:")
    print(f"Email ID: {result['id']}")
    print(f"From: {result['metadata']['from']}")
    print(f"Subject: {result['metadata']['subject']}")
    print(f"Categories: {result['analysis']['categorization']['categories']}")
    print(f"Sentiment: {result['analysis']['sentiment']['overall']}")
    print(f"Priority: {result['priority']['level']} ({result['priority']['score']})")
    print(f"Auto-reply: {result['is_auto_reply']}")
    print(f"Keywords: {[k['word'] for k in result['analysis']['keywords']]}") 