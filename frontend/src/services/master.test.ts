import {
  preview,
  PolicyConfig,
} from "./master";

// Test fixture only. Application policy is fetched from Flask.
const policy: PolicyConfig = {
  name: "Test policy",
  basis: "percentage",
  boundary_max: 100,
  max_point: 10,
  conversion: "",
  include_failed: true,
  bands: [
    {
      letter: "F",
      min: 0,
      max: 40,
      point: 0,
      passing: false,
    },
    {
      letter: "P",
      min: 40,
      max: 90,
      point: 4,
      passing: true,
    },
    {
      letter: "O",
      min: 90,
      max: 100,
      point: 10,
      passing: true,
    },
  ],
};

describe("authoritative-policy preview", () => {
  it(
    "does not substitute zero for missing marks",
    () => {
      expect(
        preview("100", "40", "", policy),
      ).toContain("Incomplete");
    },
  );

  it.each(["-1", "101", "NaN"])(
    "rejects invalid marks %s",
    (mark) => {
      expect(
        preview("100", "40", mark, policy),
      ).toContain("Invalid");
    },
  );

  it("includes the highest boundary", () => {
    expect(
      preview("100", "40", "100", policy),
    ).toBe(
      "O · 10.00 points · Pass (preview)",
    );
  });

  it(
    "uses the subject minimum even when the percentage band passes",
    () => {
      expect(
        preview("100", "95", "90", policy),
      ).toContain(
        "F · 0.00 points · Fail",
      );
    },
  );

  it("supports absolute marks", () => {
    expect(
      preview("100", "40", "90", {
        ...policy,
        basis: "marks",
      }),
    ).toContain("O");

    expect(
      preview("200", "40", "90", {
        ...policy,
        basis: "marks",
      }),
    ).toContain("Invalid");
  });
});
