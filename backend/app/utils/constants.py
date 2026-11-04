"""Enumerations shared by models, schemas and services."""

ROLES = ("student", "admin")

APPLICATION_STATUSES = (
    "interested",
    "preparing_documents",
    "ready_to_apply",
    "applied",
    "approved",
    "rejected",
)
APPLICATION_STATUS_LABELS = {
    "interested": "Interested",
    "preparing_documents": "Preparing Documents",
    "ready_to_apply": "Ready to Apply",
    "applied": "Applied",
    "approved": "Approved",
    "rejected": "Rejected",
}

VERIFICATION_STATUSES = ("unverified", "verified", "needs_review", "expired")

PROVIDER_TYPES = ("central_government", "state_government", "university", "institution", "private", "other")

SCHOLARSHIP_TYPES = (
    "merit", "need_based", "merit_cum_means", "minority", "disability",
    "sports", "research", "girl_students", "other",
)

EDUCATION_LEVELS = (
    "pre_matric", "post_matric", "diploma", "undergraduate",
    "postgraduate", "doctoral", "other",
)

ELIGIBILITY_CRITERIA = (
    "education_level", "income", "category", "gender", "state",
    "academic", "domicile", "age", "other",
)

ACHIEVEMENT_CATEGORIES = (
    "academic", "technical", "sports", "cultural", "leadership", "certifications", "other",
)

NOTIFICATION_KINDS = ("deadline_reminder", "application_update", "system", "account")
DELIVERY_CHANNELS = ("in_app", "email", "sms")
DELIVERY_STATUSES = ("pending", "sent", "failed", "skipped")

REPORT_REASONS = ("wrong_deadline", "broken_link", "wrong_eligibility", "wrong_amount", "expired", "other")
REPORT_STATUSES = ("open", "reviewing", "resolved", "dismissed")

# Generic document *types* commonly requested by Indian scholarship schemes.
# Each scholarship record lists its own required documents; this is only a vocabulary.
STANDARD_DOCUMENT_TYPES = {
    "aadhaar": "Aadhaar Card",
    "photograph": "Passport-size Photograph",
    "income_certificate": "Income Certificate",
    "caste_certificate": "Caste / Community Certificate",
    "domicile_certificate": "Domicile / Residence Certificate",
    "previous_marks_card": "Previous Year Marks Card",
    "bonafide_certificate": "Bonafide / Study Certificate",
    "fee_receipt": "Fee Receipt",
    "bank_passbook": "Bank Passbook / Account Details",
    "disability_certificate": "Disability Certificate",
    "admission_letter": "Admission Letter",
    "other": "Other",
}

INDIAN_STATES_AND_UTS = (
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka",
    "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
)
