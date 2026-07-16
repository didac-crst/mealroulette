import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/client";
import { PasswordSettingsPage } from "./PasswordSettingsPage";

const changePassword = vi.fn();

vi.mock("../../api/auth", () => ({
  changePassword: (...args: unknown[]) => changePassword(...args),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    accessToken: "token",
  }),
}));

describe("PasswordSettingsPage", () => {
  beforeEach(() => {
    changePassword.mockReset();
  });

  it("submits a password change and shows success", async () => {
    changePassword.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <PasswordSettingsPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "oldpassword" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "newpassword" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "newpassword" } });
    fireEvent.click(screen.getByRole("button", { name: "Update password" }));

    await waitFor(() => {
      expect(changePassword).toHaveBeenCalledWith("token", {
        current_password: "oldpassword",
        new_password: "newpassword",
      });
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Password updated.");
  });

  it("shows a confirmation mismatch without calling the API", async () => {
    render(
      <MemoryRouter>
        <PasswordSettingsPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "oldpassword" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "newpassword" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "otherpass" } });
    fireEvent.click(screen.getByRole("button", { name: "Update password" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("New password and confirmation do not match.");
    expect(changePassword).not.toHaveBeenCalled();
  });

  it("surfaces API failures without implying success", async () => {
    changePassword.mockRejectedValue(new ApiError("Current password is incorrect", 400));

    render(
      <MemoryRouter>
        <PasswordSettingsPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "oldpassword" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "newpassword" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "newpassword" } });
    fireEvent.click(screen.getByRole("button", { name: "Update password" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Current password is incorrect");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
