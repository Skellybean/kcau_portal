import React, { useState } from "react";
import { Text, View } from "react-native";

import { ApiError, api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { Banner, Button, Screen, TextField } from "../components";
import { colors, serif, space, type } from "../theme";
import { emailError } from "../utils/email";

export default function LoginScreen({ navigation }) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    const next = {};
    const emailProblem = emailError(email);
    if (emailProblem) next.email = emailProblem;
    if (!password) next.password = "Enter your password.";
    setErrors(next);
    setBanner(null);
    if (Object.keys(next).length) return;

    setBusy(true);
    try {
      const result = await api.post("/auth/login/", { email: email.trim().toLowerCase(), password }, { auth: false });
      await signIn(result);
    } catch (error) {
      if (error instanceof ApiError && error.data && error.data.code === "email_not_verified") {
        try {
          await api.post("/auth/resend-code/", { email: email.trim().toLowerCase() }, { auth: false });
        } catch (ignored) {
          // The verify screen offers a resend button.
        }
        navigation.navigate("Verify", { email: email.trim().toLowerCase() });
      } else {
        setBanner(error.message);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen top keyboard contentStyle={{ paddingTop: space.xxl }}>
      <View style={{ marginBottom: space.xxl }}>
        <Text style={[type.label, { color: colors.accent }]}>KCA University</Text>
        <Text style={[type.display, { fontSize: 38, lineHeight: 44, marginTop: space.sm }]}>Virtual Campus</Text>
        <Text style={[type.body, { color: colors.inkSoft, marginTop: space.md }]}>
          Your units, timetable, results and notices in one place. Sign in with your KCA email.
        </Text>
      </View>

      <Banner message={banner} />
      <TextField
        label="KCA email"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        keyboardType="email-address"
        autoCapitalize="none"
        autoCorrect={false}
        autoComplete="email"
        textContentType="username"
        placeholder="name@students.kcau.ac.ke"
      />
      <TextField
        label="Password"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        secure
        autoCapitalize="none"
        autoComplete="password"
        textContentType="password"
        onSubmitEditing={submit}
      />
      <Button title="Sign in" onPress={submit} loading={busy} />
      <Button title="Forgot password" variant="quiet" onPress={() => navigation.navigate("ForgotPassword")} style={{ marginTop: space.sm }} />

      <View style={{ marginTop: space.xl, borderTopWidth: 1, borderTopColor: colors.line, paddingTop: space.xl }}>
        <Text style={[type.heading, { fontFamily: serif }]}>New here?</Text>
        <Text style={[type.small, { marginTop: space.xs, marginBottom: space.md }]}>
          Accounts are limited to KCA students and lecturers. You will confirm your email with a code.
        </Text>
        <Button title="Create an account" variant="secondary" onPress={() => navigation.navigate("Register")} />
      </View>
    </Screen>
  );
}
