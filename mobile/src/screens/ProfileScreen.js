import React, { useState } from "react";
import { Text } from "react-native";

import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { Banner, Button, Card, Row, Screen, SectionLabel, TextField } from "../components";
import { space, type } from "../theme";
import { roleLabel } from "../utils/format";

export default function ProfileScreen() {
  const { user, updateUser, signOut } = useAuth();
  const [fullName, setFullName] = useState(user.full_name);
  const [programme, setProgramme] = useState(user.programme || "");
  const [year, setYear] = useState(user.year_of_study ? String(user.year_of_study) : "");
  const [banner, setBanner] = useState(null);
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const isStudent = user.role === "student";

  async function save() {
    setBanner(null);
    setSaved(false);
    if (!fullName.trim()) {
      setBanner("Your name cannot be empty.");
      return;
    }
    const yearNumber = year.trim() ? Number(year) : null;
    if (yearNumber !== null && (!Number.isInteger(yearNumber) || yearNumber < 1 || yearNumber > 8)) {
      setBanner("Year of study must be a number from 1 to 8.");
      return;
    }
    setBusy(true);
    try {
      const updated = await api.patch("/auth/me/", {
        full_name: fullName.trim(),
        ...(isStudent ? { programme: programme.trim(), year_of_study: yearNumber } : {}),
      });
      updateUser(updated);
      setSaved(true);
    } catch (error) {
      setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen keyboard>
      <Card style={{ paddingVertical: 0 }}>
        <Row label="Email" value={user.email} />
        <Row label="Role" value={roleLabel(user.role)} />
        {isStudent ? <Row label="Admission number" value={user.admission_number} /> : null}
      </Card>
      <Text style={[type.small, { marginTop: space.xs }]}>Your email and role come from KCA and cannot be changed here.</Text>

      <SectionLabel>Edit profile</SectionLabel>
      <Banner message={banner} />
      <Banner message={saved ? "Profile saved." : null} tone="info" />
      <TextField label="Full name" value={fullName} onChangeText={setFullName} />
      {isStudent ? (
        <>
          <TextField label="Programme" value={programme} onChangeText={setProgramme} />
          <TextField label="Year of study" value={year} onChangeText={setYear} keyboardType="number-pad" maxLength={1} />
        </>
      ) : null}
      <Button title="Save changes" onPress={save} loading={busy} />
      <Button title="Sign out" variant="secondary" onPress={signOut} style={{ marginTop: space.xl }} />
    </Screen>
  );
}
