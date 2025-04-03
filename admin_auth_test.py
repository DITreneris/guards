"""
Test script for admin authentication functionality.
This script tests:
1. Admin user creation and initialization
2. Password hashing
3. Authentication
4. Password updates
"""

import os
import sys
import json
import logging
from admin_auth import (
    init_admin_users, 
    get_admin_users, 
    authenticate, 
    create_admin_user, 
    update_admin_password,
    hash_password,
    ADMIN_FILE
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_tests():
    """Run all admin authentication tests"""
    test_count = 0
    passed_count = 0
    
    # Test 1: Initialize default admin user
    test_count += 1
    logger.info("Test 1: Initialize default admin user")
    
    # Use a test file to avoid affecting production data
    test_admin_file = 'test_admin_users.json'
    
    # Set environment variables
    original_admin_file = os.environ.get('ADMIN_FILE')
    original_default_user = os.environ.get('DEFAULT_ADMIN_USER')
    original_default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
    
    # Set test environment variables
    os.environ['ADMIN_FILE'] = test_admin_file
    os.environ['DEFAULT_ADMIN_USER'] = 'testadmin'
    os.environ['DEFAULT_ADMIN_PASSWORD'] = 'testpassword'
    
    # Remove test file if it exists
    if os.path.exists(test_admin_file):
        os.remove(test_admin_file)
    
    # Reset the module-level ADMIN_FILE variable
    import admin_auth
    admin_auth.ADMIN_FILE = test_admin_file
    
    result = init_admin_users()
    if result:
        logger.info("✓ Default admin user initialized successfully")
        passed_count += 1
    else:
        logger.error("✗ Failed to initialize default admin user")
    
    # Test 2: Get admin users
    test_count += 1
    logger.info("Test 2: Get admin users")
    
    admin_users = get_admin_users()
    if admin_users and 'testadmin' in admin_users:
        logger.info("✓ Admin users retrieved successfully")
        passed_count += 1
    else:
        logger.error("✗ Failed to retrieve admin users")
        logger.error(f"Admin users content: {admin_users}")
    
    # Test 3: Authenticate with correct credentials
    test_count += 1
    logger.info("Test 3: Authenticate with correct credentials")
    
    if authenticate('testadmin', 'testpassword'):
        logger.info("✓ Authentication successful with correct credentials")
        passed_count += 1
    else:
        logger.error("✗ Authentication failed with correct credentials")
    
    # Test 4: Authenticate with incorrect credentials
    test_count += 1
    logger.info("Test 4: Authenticate with incorrect credentials")
    
    if not authenticate('testadmin', 'wrongpassword'):
        logger.info("✓ Authentication rejected with incorrect credentials")
        passed_count += 1
    else:
        logger.error("✗ Authentication passed with incorrect credentials")
    
    # Test 5: Create new admin user
    test_count += 1
    logger.info("Test 5: Create new admin user")
    
    if create_admin_user('newuser', 'newpassword'):
        logger.info("✓ New admin user created successfully")
        passed_count += 1
    else:
        logger.error("✗ Failed to create new admin user")
    
    # Test 6: Authenticate with new user
    test_count += 1
    logger.info("Test 6: Authenticate with new user")
    
    if authenticate('newuser', 'newpassword'):
        logger.info("✓ Authentication successful with new user")
        passed_count += 1
    else:
        logger.error("✗ Authentication failed with new user")
    
    # Test 7: Update user password
    test_count += 1
    logger.info("Test 7: Update user password")
    
    if update_admin_password('newuser', 'updatedpassword'):
        logger.info("✓ Password updated successfully")
        passed_count += 1
    else:
        logger.error("✗ Failed to update password")
    
    # Test 8: Authenticate with updated password
    test_count += 1
    logger.info("Test 8: Authenticate with updated password")
    
    if authenticate('newuser', 'updatedpassword'):
        logger.info("✓ Authentication successful with updated password")
        passed_count += 1
    else:
        logger.error("✗ Authentication failed with updated password")
    
    # Test 9: Authenticate with old password after update
    test_count += 1
    logger.info("Test 9: Authenticate with old password after update")
    
    if not authenticate('newuser', 'newpassword'):
        logger.info("✓ Authentication rejected with old password")
        passed_count += 1
    else:
        logger.error("✗ Authentication passed with old password")
    
    # Test 10: Password hashing is working
    test_count += 1
    logger.info("Test 10: Password hashing is working")
    
    # Get user data
    admin_users = get_admin_users()
    user = admin_users.get('newuser', {})
    
    if user and 'salt' in user and 'password_hash' in user:
        # Hash the password with the same salt
        password_hash = hash_password('updatedpassword', user['salt'])
        
        if password_hash == user['password_hash']:
            logger.info("✓ Password hashing is working correctly")
            passed_count += 1
        else:
            logger.error("✗ Password hashing is not working correctly")
    else:
        logger.error("✗ User data not found or incomplete")
    
    # Clean up
    if os.path.exists(test_admin_file):
        os.remove(test_admin_file)
    
    # Restore original environment variables
    if original_admin_file:
        os.environ['ADMIN_FILE'] = original_admin_file
    else:
        os.environ.pop('ADMIN_FILE', None)
        
    if original_default_user:
        os.environ['DEFAULT_ADMIN_USER'] = original_default_user
    else:
        os.environ.pop('DEFAULT_ADMIN_USER', None)
        
    if original_default_password:
        os.environ['DEFAULT_ADMIN_PASSWORD'] = original_default_password
    else:
        os.environ.pop('DEFAULT_ADMIN_PASSWORD', None)
    
    # Restore the module-level ADMIN_FILE variable
    admin_auth.ADMIN_FILE = os.getenv('ADMIN_FILE', 'admin_users.json')
    
    # Summary
    logger.info(f"Tests completed: {passed_count}/{test_count} passed")
    
    if passed_count == test_count:
        logger.info("✅ All tests passed successfully!")
        return True
    else:
        logger.error("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 