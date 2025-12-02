# InsightShop User Credentials

This document contains all user credentials for the InsightShop application. These users are automatically created when running the `scripts/seed_users.py` script.

## ⚠️ Security Notice

**IMPORTANT**: This file contains sensitive credentials. In production environments:
- Do NOT commit this file to public repositories
- Store credentials securely using environment variables or secret management systems
- Rotate passwords regularly
- Use strong, unique passwords for production

## User Roles

### Superadmin
- **Access Level**: Full system access
- **Permissions**: Can access admin panel, manage all system settings, users, products, sales, etc.
- **Restrictions**: None

### Regular Users (Members)
- **Access Level**: Member area only
- **Permissions**: Can view orders, payments, and account information
- **Restrictions**: Cannot access admin panel

---

## Superadmin User

| Field | Value |
|-------|-------|
| **Email** | `superadmin@insightshop.com` |
| **Password** | `Super12345` |
| **First Name** | Super |
| **Last Name** | Admin |
| **Role** | Superadmin |
| **Status** | Verified |
| **Access** | Full Admin Panel Access |

### Login Instructions
1. Navigate to the login page
2. Enter email: `superadmin@insightshop.com`
3. Enter password: `Super12345`
4. Click "Login"
5. You will have access to the Admin panel via the navbar

---

## Demo Users (Regular Members)

All demo users have the same password for easy testing: `Demo12345`

### User 1: John Doe
| Field | Value |
|-------|-------|
| **Email** | `john.doe@example.com` |
| **Password** | `Demo12345` |
| **First Name** | John |
| **Last Name** | Doe |
| **Role** | Regular User |
| **Status** | Verified |
| **Access** | Member Area Only |

### User 2: Jane Smith
| Field | Value |
|-------|-------|
| **Email** | `jane.smith@example.com` |
| **Password** | `Demo12345` |
| **First Name** | Jane |
| **Last Name** | Smith |
| **Role** | Regular User |
| **Status** | Verified |
| **Access** | Member Area Only |

### User 3: Mike Johnson
| Field | Value |
|-------|-------|
| **Email** | `mike.johnson@example.com` |
| **Password** | `Demo12345` |
| **First Name** | Mike |
| **Last Name** | Johnson |
| **Role** | Regular User |
| **Status** | Verified |
| **Access** | Member Area Only |

### User 4: Sarah Williams
| Field | Value |
|-------|-------|
| **Email** | `sarah.williams@example.com` |
| **Password** | `Demo12345` |
| **First Name** | Sarah |
| **Last Name** | Williams |
| **Role** | Regular User |
| **Status** | Verified |
| **Access** | Member Area Only |

### User 5: David Brown
| Field | Value |
|-------|-------|
| **Email** | `david.brown@example.com` |
| **Password** | `Demo12345` |
| **First Name** | David |
| **Last Name** | Brown |
| **Role** | Regular User |
| **Status** | Verified |
| **Access** | Member Area Only |

---

## Quick Reference

### Superadmin
```
Email: superadmin@insightshop.com
Password: Super12345
```

### Demo Users (All)
```
Email: [user]@example.com
Password: Demo12345
```

Where `[user]` is one of:
- `john.doe`
- `jane.smith`
- `mike.johnson`
- `sarah.williams`
- `david.brown`

---

## Creating/Updating Users

To create or update these users, run:

```bash
python scripts/seed_users.py
```

This script will:
1. Add the `is_superadmin` column to the users table if it doesn't exist
2. Create the superadmin user if it doesn't exist
3. Create all demo users if they don't exist
4. Update existing users with correct roles and passwords

---

## Access Control

### Admin Panel (`/admin`)
- **Allowed**: Only users with `is_superadmin = True`
- **Redirect**: Non-superadmin users are redirected to `/members`
- **Features**: 
  - Fashion Knowledge Base management
  - User management
  - Product management
  - Sales management
  - Payment logs
  - Reviews management

### Member Area (`/members`)
- **Allowed**: All authenticated users
- **Features**:
  - View all orders
  - View payment history
  - View account statistics
  - Product suggestions

---

## Password Requirements

- Minimum 8 characters
- Recommended: Mix of uppercase, lowercase, numbers, and special characters
- Current passwords are set for development/testing purposes only

---

## Notes

- All users are pre-verified (`is_verified = True`)
- Demo users have `is_admin = False` and `is_superadmin = False`
- Superadmin has both `is_admin = True` and `is_superadmin = True`
- Passwords are hashed using bcrypt before storage
- Users can change their passwords after login

---

## Last Updated

This document was last updated when the user seeding system was implemented.

