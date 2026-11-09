import React, { useEffect, useState } from "react";
import { Text } from "react-native";

import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { Banner, Button, Screen, TextField } from "../components";
import { space, type } from "../theme";

const COOLDOWN = 30;

export default function VerifyScreen({ route }) {
  const { email } = route.params;
  const { signIn } = useAuth();
  const [code, setCode] = useState("");
  const [banner, setBanner] = useState(null);
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [wait, setWait] = useState(COOLDOWN);

  useEffect(() => {
    if (wait <= 0) return undefined;
    const timer = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(timer);
  }, [wait]);

  async function submit() {
    if (code.length !== 6) {
      setBanner("Enter the 6-digit code from your email.");
      return;
    }
    setBusy(true);
    setBanner(null);
    try {
      const result = await api.post("/auth/verify/", { email, code }, { auth: false });
      await signIn(result);
    } catch (error) {
      setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    setBanner(null);
    try {
      await api.post("/auth/resend-code/", { email }, { auth: false });
      setNotice("A new code is on its way.");
      setWait(COOLDOWN);
    } catch (error) {
      setBanner(error.message);
    }
  }

  return (
    <Screen keyboard>
      <Text style={[type.title, { marginBottom: space.sm }]}>Check your inbox</Text>
      <Text style={[type.body, { color: "#4A5663", marginBottom: space.xl }]}>
        We sent a 6-digit code to {email}. It expires in 15 minutes.
      </Text>
      <Banner message={banner} />
      <Banner message={notice} tone="info" />
      <TextField
        label="Verification code"
        value={code}
        onChangeText={(value) => setCode(value.replace(/\D/g, "").slice(0, 6))}
        keyboardType="number-pad"
        maxLength={6}
        autoComplete="one-time-code"
        textContentType="oneTimeCode"
        placeholder="000000"
        onSubmitEditing={submit}
      />
      <Button title="Verify and continue" onPress={submit} loading={busy} />
      <Button
        title={wait > 0 ? `Send a new code in ${wait}s` : "Send a new code"}
        variant="quiet"
        disabled={wait > 0}
        onPress={resend}
        style={{ marginTop: space.sm }}
      />
    </Screen>
  );
}
