export interface User { id: number; email: string; role: "student" | "admin"; is_active: boolean;
  email_verified: boolean; full_name: string | null; last_login_at: string | null; created_at: string; }
export interface Meta { page: number; per_page: number; total: number; pages: number; }
export interface Category { id: number; name: string; slug: string; description: string | null; scholarship_count?: number; }
export interface Eligibility { id?: number; criterion_type: string; value: string | null; numeric_value: number | null; description: string; }
export interface RequiredDoc { id?: number; document_type: string; document_type_label?: string; name: string; is_mandatory: boolean; notes: string | null; }
export interface ScholarshipSummary { id: number; title: string; slug: string; provider_name: string; provider_type: string;
  scholarship_type: string; category: Category | null; state: string | null; academic_year: string | null;
  amount_text: string | null; amount_max: number | null; application_open_date: string | null;
  application_close_date: string | null; days_left: number | null; education_levels: string[];
  verification_status: string; effective_status: string; last_verified_at: string | null;
  official_source_name: string; is_published: boolean; }
export interface ScholarshipDetail extends ScholarshipSummary { description: string | null; benefits: string | null;
  source_url: string; application_url: string; verification_notes: string | null; eligibility: Eligibility[];
  required_documents: RequiredDoc[]; tracking?: { is_bookmarked: boolean; reminders_enabled: boolean } | null;
  application?: Application | null; publish_problems?: string[]; category_id?: number | null; }
export interface Application { id: number; scholarship_id: number; scholarship: ScholarshipSummary | null; status: string;
  status_label: string; applied_on: string | null; application_reference: string | null; notes: string | null;
  history?: { from_status: string | null; to_status: string; to_status_label: string; note: string | null; changed_at: string }[]; }
export interface Tracked { id: number; scholarship: ScholarshipSummary; is_bookmarked: boolean; reminders_enabled: boolean; application: Application | null; }
export interface Grade { label: string; grade_point: number; counts_in_gpa: boolean; is_passing?: boolean; sort_order?: number; }
export interface Scale { id: number; name: string; description: string | null; max_grade_point: number; is_template: boolean; is_owned: boolean; grades: Grade[]; }
export interface Subject { id: number; name: string; code: string | null; credits: number; grade_label: string; grade_point: number; counts_in_gpa: boolean; }
export interface Semester { id: number; number: number; title: string; academic_year: string | null; notes: string | null;
  grading_scale_id: number | null; grading_scale_name: string | null; sgpa: number | null; total_credits: number; subjects?: Subject[]; }
export interface Achievement { id: number; title: string; description: string | null; organization: string | null; category: string;
  achieved_on: string; rank_position: string | null; location_name: string | null; latitude: number | null; longitude: number | null;
  is_public?: boolean; certificate_document_id?: number | null; certificate_name?: string | null; certificate_mime?: string | null; }
export interface Doc { id: number; display_name: string; original_filename: string; mime_type: string; size_bytes: number;
  document_type: string; document_type_label: string; folder_id: number | null; folder_name: string | null;
  issued_on: string | null; expires_on: string | null; days_to_expiry: number | null; is_expired: boolean; previewable: boolean; created_at: string; }
export interface Delivery { channel: string; status: string; attempts: number; last_error: string | null; sent_at: string | null; }
export interface Notification { id: number; kind: string; title: string; message: string; link: string | null;
  is_read: boolean; created_at: string; deliveries: Delivery[]; }
export interface Vocab { states: string[]; education_levels: string[]; scholarship_types: string[]; provider_types: string[];
  eligibility_criteria: string[]; achievement_categories: string[]; application_statuses: { value: string; label: string }[];
  document_types: Record<string, string>; verification_statuses: string[]; report_reasons: string[]; report_statuses: string[]; reminder_days: number[]; }
