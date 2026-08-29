// apps/web/__tests__/ui-primitives.test.tsx — shadcn/ui primitives smoke test
// Story 0.5 — T2.8 (AC #2)
//
// Smoke test that the manually-authored shadcn primitives render correctly
// and respond to user interaction. Full test suite activates in AC #4 (T4 vitest wire).

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

describe("Tabs primitive", () => {
  it("renders TabsList with two triggers and the default content visible", () => {
    render(
      <Tabs defaultValue="t1">
        <TabsList>
          <TabsTrigger value="t1">Tab 1</TabsTrigger>
          <TabsTrigger value="t2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="t1">Content 1</TabsContent>
        <TabsContent value="t2">Content 2</TabsContent>
      </Tabs>,
    );

    expect(screen.getByRole("tab", { name: "Tab 1" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Tab 2" })).toBeInTheDocument();
    expect(screen.getByText("Content 1")).toBeVisible();
  });

  it("switches content when a different trigger is clicked", async () => {
    const user = userEvent.setup();
    render(
      <Tabs defaultValue="t1">
        <TabsList>
          <TabsTrigger value="t1">Tab 1</TabsTrigger>
          <TabsTrigger value="t2">Tab 2</TabsTrigger>
        </TabsList>
        <TabsContent value="t1">Content 1</TabsContent>
        <TabsContent value="t2">Content 2</TabsContent>
      </Tabs>,
    );

    await user.click(screen.getByRole("tab", { name: "Tab 2" }));

    // After click, Radix switches state and Content 2 becomes visible.
    expect(screen.getByRole("tab", { name: "Tab 2" })).toHaveAttribute(
      "data-state",
      "active",
    );
    expect(
      screen.getByRole("tabpanel", { name: "Tab 2" }),
    ).toHaveTextContent("Content 2");
  });
});
