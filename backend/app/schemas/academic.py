from marshmallow import ValidationError, fields, validate, validates_schema

from app.schemas.common import BaseSchema, trimmed


class GradeMappingInSchema(BaseSchema):
    label = fields.String(required=True, validate=validate.Length(min=1, max=10))
    grade_point = fields.Decimal(required=True, places=2, validate=validate.Range(0, 100))
    min_percent = fields.Decimal(allow_none=True, places=2, validate=validate.Range(0, 100))
    max_percent = fields.Decimal(allow_none=True, places=2, validate=validate.Range(0, 100))
    counts_in_gpa = fields.Boolean(load_default=True)
    is_passing = fields.Boolean(load_default=True)
    sort_order = fields.Integer(load_default=0)


class GradingScaleSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    description = trimmed(500)
    max_grade_point = fields.Decimal(required=True, places=2, validate=validate.Range(1, 100))
    grades = fields.List(fields.Nested(GradeMappingInSchema), required=True, validate=validate.Length(min=1))

    @validates_schema
    def _check(self, data, **_):
        labels = [g["label"].strip().upper() for g in data.get("grades", [])]
        if len(labels) != len(set(labels)):
            raise ValidationError({"grades": ["Grade labels must be unique."]})
        top = data.get("max_grade_point")
        if top is not None and any(g["grade_point"] > top for g in data.get("grades", [])):
            raise ValidationError({"grades": ["A grade point exceeds max_grade_point."]})


class SemesterSchema(BaseSchema):
    number = fields.Integer(required=True, validate=validate.Range(1, 20))
    title = trimmed(100)
    academic_year = trimmed(20)
    notes = trimmed(500)
    grading_scale_id = fields.Integer(required=True)


class SubjectSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=200))
    code = trimmed(30)
    credits = fields.Decimal(required=True, places=2, validate=validate.Range(0, 50))
    grade_label = fields.String(required=True, validate=validate.Length(min=1, max=10))
