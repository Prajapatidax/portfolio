import re
from typing import Dict, Any, Tuple, List

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,10}$")
PHONE_REGEX = re.compile(r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$")

VALID_PROJECT_TYPES = {
    "Personal Website",
    "Business Website",
    "Portfolio Website",
    "Landing Page",
    "E-commerce Website",
    "SaaS Platform",
    "Web Application",
    "Admin Dashboard",
    "Other",
}

VALID_BUDGET_RANGES = {
    "Under ₹5,000",
    "₹5,000–₹10,000",
    "₹10,000–₹25,000",
    "₹25,000–₹50,000",
    "₹50,000+",
    "Not decided yet",
}


def is_valid_email(email: str) -> bool:
    if not email or len(email) > 150:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    if not phone:
        return True
    phone = phone.strip()
    return bool(PHONE_REGEX.match(phone)) or len(re.sub(r"\D", "", phone)) >= 8


def validate_quotation_payload(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    errors: Dict[str, str] = {}
    if not isinstance(data, dict):
        return False, {"general": "Invalid request format"}

    # Project Type
    project_type = data.get("project_type", "").strip()
    if not project_type or project_type not in VALID_PROJECT_TYPES:
        errors["project_type"] = f"Please select a valid project type from: {', '.join(sorted(VALID_PROJECT_TYPES))}"

    # Customer Name
    customer_name = data.get("customer_name", "").strip()
    if not customer_name or len(customer_name) < 2:
        errors["customer_name"] = "Full name must be at least 2 characters"
    elif len(customer_name) > 100:
        errors["customer_name"] = "Full name cannot exceed 100 characters"

    # Customer Email
    customer_email = data.get("customer_email", "").strip()
    if not is_valid_email(customer_email):
        errors["customer_email"] = "Please provide a valid email address"

    # Customer Phone (optional)
    customer_phone = data.get("customer_phone", "").strip()
    if customer_phone and not is_valid_phone(customer_phone):
        errors["customer_phone"] = "Please enter a valid phone number"

    # Project Name
    project_name = data.get("project_name", "").strip()
    if not project_name or len(project_name) < 2:
        errors["project_name"] = "Project name is required (min 2 characters)"
    elif len(project_name) > 150:
        errors["project_name"] = "Project name cannot exceed 150 characters"

    # Project Description
    project_description = data.get("project_description", "").strip()
    if not project_description or len(project_description) < 10:
        errors["project_description"] = "Please provide a detailed project description (min 10 characters)"
    elif len(project_description) > 5000:
        errors["project_description"] = "Project description cannot exceed 5,000 characters"

    # Budget Range
    budget_range = data.get("budget_range", "").strip()
    if not budget_range or budget_range not in VALID_BUDGET_RANGES:
        errors["budget_range"] = "Please select a valid budget range"

    # Timeline
    timeline = data.get("timeline", "").strip()
    if not timeline:
        errors["timeline"] = "Expected completion timeline is required"

    # Selected Designs
    selected_designs = data.get("selected_designs", [])
    if not isinstance(selected_designs, list):
        errors["selected_designs"] = "Selected designs must be a list"

    # Features
    features = data.get("features", [])
    if not isinstance(features, list):
        errors["features"] = "Features must be a list"

    return len(errors) == 0, errors


def validate_contact_payload(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    errors: Dict[str, str] = {}
    if not isinstance(data, dict):
        return False, {"general": "Invalid data format"}

    name = data.get("name", "").strip()
    if not name or len(name) < 2:
        errors["name"] = "Name must be at least 2 characters"
    elif len(name) > 150:
        errors["name"] = "Name cannot exceed 150 characters"

    email = data.get("email", "").strip()
    if not is_valid_email(email):
        errors["email"] = "Please provide a valid email address"

    subject = data.get("subject", "").strip()
    if not subject or len(subject) < 2:
        errors["subject"] = "Subject is required (min 2 characters)"
    elif len(subject) > 200:
        errors["subject"] = "Subject cannot exceed 200 characters"

    message = data.get("message", "").strip()
    if not message or len(message) < 5:
        errors["message"] = "Message must be at least 5 characters"
    elif len(message) > 5000:
        errors["message"] = "Message cannot exceed 5000 characters"

    return len(errors) == 0, errors

