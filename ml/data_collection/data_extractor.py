#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Extraction Module
Extracts structured data from unstructured text.
"""

import re
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime

from ml.config import get_data_extraction_config
from ml.storage import extraction_storage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataExtractor:
    """
    Extracts structured data from unstructured text.
    """
    
    def __init__(self):
        """Initialize data extractor."""
        self.config = get_data_extraction_config()
        self.confidence_thresholds = self.config.get('confidence_thresholds', {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.3
        })
        self.validation_threshold = self.config.get('validation', {}).get('threshold', 0.6)
        self.enable_validation = self.config.get('validation', {}).get('enable_automated_validation', True)
        logger.info("Data Extractor initialized")
    
    def extract_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: Text to extract data from
            
        Returns:
            Dictionary with extraction results
        """
        if not text:
            logger.warning("Empty text provided for extraction")
            return {
                "error": "Empty text provided",
                "confidence": 0.0,
                "entity_count": 0,
                "entities": {},
                "requires_validation": True,
                "customer": {},
                "product": {}
            }
        
        # Extract entities using regex patterns
        entities = self._extract_entities_regex(text)
        
        # Extract using dictionary lookup
        additional_entities = self._extract_entities_dictionary(text)
        
        # Merge entity results
        for entity_type, values in additional_entities.items():
            if entity_type not in entities:
                entities[entity_type] = values
            else:
                # Merge values, avoiding duplicates
                entities[entity_type].extend([v for v in values if v not in entities[entity_type]])
        
        # Extract customer information
        customer_info = self._extract_customer_info(text, entities)
        
        # Extract product information
        product_info = self._extract_product_info(text, entities)
        
        # Calculate confidence
        confidence = self._calculate_confidence(entities, customer_info, product_info)
        
        # Determine if validation is required
        requires_validation = confidence < self.validation_threshold if self.enable_validation else False
        
        # Count entities
        entity_count = sum(len(values) for values in entities.values())
        
        # Prepare results
        results = {
            "confidence": confidence,
            "entity_count": entity_count,
            "entities": entities,
            "requires_validation": requires_validation,
            "customer": customer_info,
            "product": product_info
        }
        
        logger.info(f"Extracted {entity_count} entities with confidence {confidence:.2f}")
        return results
    
    def _extract_entities_regex(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using regex patterns.
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary of entity types and their values
        """
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "version": r'\b\d+\.\d+(\.\d+)?\b',
            "mac_address": r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b',
            "url": r'https?://[^\s<>"]+|www\.[^\s<>"]+',
            "date": r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}\b',
            "error_code": r'\b(?:ERR|ERROR)[-:]\d+\b',
            "license_key": r'\b[A-Z0-9]{2,}-[A-Z0-9]{4,}-[A-Z0-9]{4,}\b'
        }
        
        entities = {}
        
        for entity_type, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                # Remove duplicates while preserving order
                seen = set()
                unique_matches = [m for m in matches if not (m in seen or seen.add(m))]
                entities[entity_type] = unique_matches
        
        return entities
    
    def _extract_entities_dictionary(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities using dictionary lookup.
        
        Args:
            text: Text to extract from
            
        Returns:
            Dictionary of entity types and their values
        """
        dictionaries = {
            "product": [
                "ARP Guard", "ARP Guard Pro", "ARP Guard Enterprise", 
                "Evader", "Evader Pro", "Evader Enterprise",
                "Network Sentinel", "Packet Analyzer"
            ],
            "issue_type": [
                "false positive", "false alarm", "error", "crash", "bug",
                "not working", "performance issue", "slow", "timeout",
                "security breach", "attack", "vulnerability"
            ],
            "network_device": [
                "router", "switch", "firewall", "access point", "gateway",
                "modem", "hub", "bridge", "repeater", "server"
            ]
        }
        
        entities = {}
        
        for entity_type, dictionary in dictionaries.items():
            matches = []
            text_lower = text.lower()
            
            for term in dictionary:
                term_lower = term.lower()
                if term_lower in text_lower:
                    # Find the original case in the text
                    index = text_lower.find(term_lower)
                    original_case = text[index:index + len(term)]
                    matches.append(original_case)
            
            if matches:
                entities[entity_type] = matches
        
        return entities
    
    def _extract_customer_info(self, text: str, entities: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Extract customer information from text and entities.
        
        Args:
            text: Text to extract from
            entities: Already extracted entities
            
        Returns:
            Dictionary with customer information
        """
        customer_info = {}
        
        # Extract name - Look for "Name:" or similar patterns
        name_match = re.search(r'(?:Name|Customer|Client)[\s:]+([A-Z][a-z]+(?: [A-Z][a-z]+){1,2})', text)
        if name_match:
            customer_info["name"] = name_match.group(1).strip()
        
        # Extract email from entities
        if "email" in entities and entities["email"]:
            customer_info["email"] = entities["email"][0]  # Take first email
        
        # Extract company - Look for "Company:" or similar patterns
        company_match = re.search(r'(?:Company|Organization|Business)[\s:]+([A-Za-z0-9]+(?: [A-Za-z0-9]+){0,5}(?:\s+Inc\.?|LLC|Ltd\.?|Corp\.?|Corporation)?)', text)
        if company_match:
            customer_info["company"] = company_match.group(1).strip()
        
        # Extract phone from entities
        if "phone" in entities and entities["phone"]:
            customer_info["phone"] = entities["phone"][0]  # Take first phone
        
        return customer_info
    
    def _extract_product_info(self, text: str, entities: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Extract product information from text and entities.
        
        Args:
            text: Text to extract from
            entities: Already extracted entities
            
        Returns:
            Dictionary with product information
        """
        product_info = {}
        
        # Extract product name from entities
        if "product" in entities and entities["product"]:
            product_info["name"] = entities["product"][0]  # Take first product
        
        # Extract version from entities
        if "version" in entities and entities["version"]:
            product_info["version"] = entities["version"][0]  # Take first version
        
        # Extract license key from entities
        if "license_key" in entities and entities["license_key"]:
            product_info["license"] = entities["license_key"][0]  # Take first license key
        
        # Try to extract deployment type (if not found in entities)
        deployment_match = re.search(r'(?:Deployment|Environment)[\s:]+([A-Za-z0-9]+(?: [A-Za-z0-9]+){0,2})', text)
        if deployment_match:
            product_info["deployment"] = deployment_match.group(1).strip()
        
        return product_info
    
    def _calculate_confidence(self, entities: Dict[str, List[str]], 
                             customer_info: Dict[str, str],
                             product_info: Dict[str, str]) -> float:
        """
        Calculate confidence score for the extraction.
        
        Args:
            entities: Extracted entities
            customer_info: Extracted customer information
            product_info: Extracted product information
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence starts at 0.3
        confidence = 0.3
        
        # More entity types increase confidence
        entity_type_count = len(entities)
        if entity_type_count >= 5:
            confidence += 0.2
        elif entity_type_count >= 3:
            confidence += 0.1
        
        # More entities increase confidence
        entity_count = sum(len(values) for values in entities.values())
        if entity_count >= 10:
            confidence += 0.2
        elif entity_count >= 5:
            confidence += 0.1
        
        # Customer information increases confidence
        if customer_info:
            if "name" in customer_info and "email" in customer_info:
                confidence += 0.15
            elif "name" in customer_info or "email" in customer_info:
                confidence += 0.05
        
        # Product information increases confidence
        if product_info:
            if "name" in product_info and "version" in product_info:
                confidence += 0.15
            elif "name" in product_info:
                confidence += 0.05
        
        # Cap at 1.0
        return min(1.0, confidence)
    
    def extract_and_store(self, text: str, source_id: str = None) -> Dict[str, Any]:
        """
        Extract data and store the results.
        
        Args:
            text: Text to extract from
            source_id: Optional ID of the data source
            
        Returns:
            Dictionary with extraction results including storage status
        """
        # Generate extraction ID
        extraction_id = str(uuid.uuid4())
        
        # Extract data
        results = self.extract_data(text)
        
        # Add metadata
        results["id"] = extraction_id
        results["source_id"] = source_id
        results["timestamp"] = datetime.now().isoformat()
        results["text_length"] = len(text)
        results["text_preview"] = text[:200] + "..." if len(text) > 200 else text
        
        # Store results
        stored = False
        if extraction_storage is not None:
            stored = extraction_storage.save_extraction(results)
            results["stored"] = stored
            
            if stored:
                logger.info(f"Stored extraction results with ID: {extraction_id}")
            else:
                logger.error(f"Failed to store extraction results with ID: {extraction_id}")
        else:
            logger.warning("Extraction storage not available, results not stored")
            results["stored"] = False
        
        return results


# Example usage
if __name__ == "__main__":
    # Create extractor
    extractor = DataExtractor()
    
    # Sample text
    sample_text = """
    Customer: John Smith
    Email: john.smith@example.com
    Company: Acme Corp
    
    Issue: ARP Guard version 0.6.0 is showing false positives
    License: AB-12345-67890
    
    The system started reporting false attacks from IP 192.168.1.100 
    after the latest update on June 15, 2023. This is happening on 
    our Cisco router with MAC address 00:1A:2B:3C:4D:5E.
    
    Error code: ERR-4502
    
    Please help resolve this issue as soon as possible.
    
    Contact: (555) 123-4567
    """
    
    # Extract data
    result = extractor.extract_data(sample_text)
    
    # Print results
    print("\nData Extraction Results:")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Entity Count: {result['entity_count']}")
    print(f"Requires Validation: {result['requires_validation']}")
    
    print("\nEntities:")
    for entity_type, entities in result['entities'].items():
        print(f"  {entity_type}: {entities}")
    
    print("\nCustomer Information:")
    for field, value in result['customer'].items():
        print(f"  {field}: {value}")
    
    print("\nProduct Information:")
    for field, value in result['product'].items():
        print(f"  {field}: {value}") 