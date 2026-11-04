import { fireEvent, render, screen } from "@testing-library/react";
import { Badge, Empty, Pager } from "./ui";
import { label } from "../../utils/format";

test("Badge humanises values", () => {
  render(<Badge value="needs_review" />);
  expect(screen.getByText("Needs Review")).toBeInTheDocument();
});

test("Empty shows title", () => {
  render(<Empty title="No scholarships yet" />);
  expect(screen.getByText("No scholarships yet")).toBeInTheDocument();
});

test("Pager calls onPage and disables at edges", () => {
  const onPage = vi.fn();
  render(<Pager page={1} pages={3} onPage={onPage} />);
  expect(screen.getByText("Previous")).toBeDisabled();
  fireEvent.click(screen.getByText("Next"));
  expect(onPage).toHaveBeenCalledWith(2);
});

test("label util", () => expect(label("ready_to_apply")).toBe("Ready To Apply"));
