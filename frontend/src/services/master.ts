export interface Band {
  letter: string;
  min: number;
  max: number;
  point: number;
  passing: boolean;
}

export interface PolicyConfig {
  name: string;
  basis: "percentage" | "marks";
  boundary_max: number;
  max_point: number;
  conversion: string;
  include_failed: boolean;
  bands: Band[];
}

export interface Policy {
  version: number;
  configuration: PolicyConfig;
}

export interface SubjectRecord {
  id: number;
  name: string;
  code: string | null;
  credits: number;
  version: number;
  maximum_marks: number | null;
  passing_marks: number | null;
  marks_obtained: number | null;
  grade: string | null;
  grade_point: number | null;
  result: string;
  included: boolean;
  legacy_grade: string | null;
}

export interface Summary {
  gpa: number | null;
  grade: string | null;
  total_credits: number;
  completed_credits: number;
  raw_percentage: number | null;
  converted_percentage: number | null;
  excluded_subjects: number;
  pending_subjects: number;
  failed_subjects: number;
}

export interface SemesterRecord extends Summary {
  number: number;
  academic_year: string | null;
  subjects: SubjectRecord[];
  sgpa: number | null;
  cumulative: Summary;
  completed: boolean;
}

export interface MasterData {
  student: {
    name: string;
    student_id: number;
    course: string | null;
    department: string | null;
  };
  policy: Policy;
  semesters: SemesterRecord[];
  total: Summary & {
    completed_semesters: number;
  };
}

export const score = (
  value: number | null | undefined,
): string => (value == null ? "—" : value.toFixed(2));

/** Preview only. Saved authoritative results always come from Flask. */
export function preview(
  maximum: string,
  passing: string,
  obtained: string,
  policy: PolicyConfig,
): string {
  if (
    [maximum, passing, obtained].some(
      (value) => value.trim() === "",
    )
  ) {
    return "Incomplete — excluded from GPA";
  }

  const [max, min, mark] = [
    maximum,
    passing,
    obtained,
  ].map(Number);

  if (
    ![max, min, mark].every(Number.isFinite) ||
    max <= 0 ||
    min < 0 ||
    mark < 0 ||
    min > max ||
    mark > max ||
    (policy.basis === "marks" &&
      max > policy.boundary_max)
  ) {
    return "Invalid marks — cannot save";
  }

  const value =
    policy.basis === "percentage"
      ? (mark / max) * 100
      : mark;

  let band = policy.bands.find(
    (candidate) =>
      value >= candidate.min &&
      (value < candidate.max ||
        (value === policy.boundary_max &&
          value === candidate.max)),
  );

  if (!band) {
    return "Invalid — no applicable band";
  }

  if (mark < min) {
    band = policy.bands[0];
  }

  return `${band.letter} · ${score(band.point)} points · ${
    band.passing && mark >= min ? "Pass" : "Fail"
  } (preview)`;
}
