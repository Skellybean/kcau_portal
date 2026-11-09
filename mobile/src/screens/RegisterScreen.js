import React, { useState } from "react";
import { Text } from "react-native";

import { api } from "../api";
import { Banner, Button, Screen, Tag, TextField } from "../components";
import { space, type } from "../theme";
import { classifyEmail, emailError } from "../utils/email";

export default function RegisterScreen({ navigation }) {
  const [form, setForm] = useState({ full_name: "", email: "", admission_number: "", password: "", confirm: "" });
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState(null);
  const [busy, setBusy] = useState(false);

  const kind = classifyEmail(form.email);
  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }));

  async function submit() {
    const next = {};
    if (!form.full_name.trim()) next.full_name = "Enter your full name.";
    const emailProblem = emailError(form.email);
    if (emailProblem) next.email = emailProblem;
    if (form.password.length < 8) next.password = "Use at least 8 characters.";
    if (form.confirm !== form.password) next.confirm = "The passwords do not match.";
    setErrors(next);
    setBanner(null);
    if (Object.keys(next).length) return;

    setBusy(true);
    try {
      const email = form.email.trim().toLowerCase();
      await api.post(
        "/auth/register/",
        {
          full_name: form.full_name.trim(),
          email,
          password: form.password,
          ...(kind === "student" && form.admission_number.trim() ? { admission_number: form.admission_number.trim() } : {}),
        },
        { auth: false }
      );
      navigation.navigate("Verify", { email });
    } catch (error) {
      setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen keyboard>
      <Text style={[type.title, { marginBottom: space.xs }]}>Create your account</Text>
      <Text style={[type.small, { marginBottom: space.xl }]}>Only KCA University email addresses are accepted.</Text>

      <Banner message={banner} />
      <TextField label="Full name" value={form.full_name} onChangeText={set("full_name")} error={errors.full_name} autoComplete="name" textContentType="name" />
      <TextField
        label="KCA email"
        value={form.email}
        onChangeText={set("email")}
        error={errors.email}
        keyboardType="email-address"
        autoCapitalize="none"
        autoCorrect={false}
        autoComplete="email"
        placeholder="name@students.kcau.ac.ke"
      />
      {kind ? (
        <Tag tone="accent">{kind === "student" ? "Student account" : "Lecturer account"}</Tag>
      ) : null}
      {kind === "student" ? (
        <TextField
          style={{ marginTop: space.lg }}
          label="Admission number (optional)"
          value={form.admission_number}
          onChangeText={set("admission_number")}
          autoCapitalize="characters"
        />
      ) : null}
      <TextField
        style={{ marginTop: space.lg }}
        label="Password"
        value={form.password}
        onChangeText={set("password")}
        error={errors.password}
        hint="At least 8 characters. Avoid common passwords."
        secure
        autoCapitalize="none"
        textContentType="newPassword"
      />
      <TextField label="Confirm password" value={form.confirm} onChangeText={set("confirm")} error={errors.confirm} secure autoCapitalize="none" textContentType="newPassword" />
      <Button title="Send verification code" onPress={submit} loading={busy} />
    </Screen>
  );
}
