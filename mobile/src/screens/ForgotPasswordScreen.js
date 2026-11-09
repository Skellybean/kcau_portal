import React, { useState } from "react";
import { Text } from "react-native";

import { api } from "../api";
import { Banner, Button, Screen, TextField } from "../components";
import { space, type } from "../theme";
import { emailError } from "../utils/email";

export default function ForgotPasswordScreen({ navigation }) {
  const [step, setStep] = useState("request");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);

  async function request() {
    const problem = emailError(email);
    setErrors({ email: problem });
    setBanner(null);
    if (problem) return;
    setBusy(true);
    try {
      await api.post("/auth/password-reset/", { email: email.trim().toLowerCase() }, { auth: false });
      setNotice("If that account exists, a code is on its way to the inbox.");
      setStep("confirm");
    } catch (error) {
      setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    const next = {};
    if (code.length !== 6) next.code = "Enter the 6-digit code.";
    if (password.length < 8) next.password = "Use at least 8 characters.";
    setErrors(next);
    setBanner(null);
    if (Object.keys(next).length) return;
    setBusy(true);
    try {
      await api.post(
        "/auth/password-reset/confirm/",
        { email: email.trim().toLowerCase(), code, new_password: password },
        { auth: false }
      );
      navigation.navigate("Login");
    } catch (error) {
      setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen keyboard>
      <Text style={[type.title, { marginBottom: space.sm }]}>Reset your password</Text>
      <Text style={[type.small, { marginBottom: space.xl }]}>We will email a code to your KCA address.</Text>
      <Banner message={banner} />
      <Banner message={notice} tone="info" />
      <TextField
        label="KCA email"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        editable={step === "request"}
        keyboardType="email-address"
        autoCapitalize="none"
        autoCorrect={false}
      />
      {step === "request" ? (
        <Button title="Send reset code" onPress={request} loading={busy} />
      ) : (
        <>
          <TextField
            label="Reset code"
            value={code}
            onChangeText={(value) => setCode(value.replace(/\D/g, "").slice(0, 6))}
            error={errors.code}
            keyboardType="number-pad"
            maxLength={6}
            autoComplete="one-time-code"
          />
          <TextField label="New password" value={password} onChangeText={setPassword} error={errors.password} secure autoCapitalize="none" textContentType="newPassword" />
          <Button title="Set new password" onPress={confirm} loading={busy} />
          <Button title="Send the code again" variant="quiet" onPress={request} style={{ marginTop: space.sm }} />
        </>
      )}
    </Screen>
  );
}
