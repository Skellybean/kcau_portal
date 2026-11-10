import React, { useState } from "react";
import { Text, View } from "react-native";

import { api } from "../api";
import { Banner, Button, Chip, Screen, TextField } from "../components";
import { DAY_NAMES, clock } from "../utils/format";
import { space, type } from "../theme";

export default function ClassLinkScreen({ route, navigation }) {
  const { slot } = route.params;
  const [mode, setMode] = useState(slot.mode || "in_person");
  const [link, setLink] = useState(slot.meeting_link || "");
  const [note, setNote] = useState(slot.meeting_note || "");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const remote = mode !== "in_person";

  async function save() {
    setError(null);
    const trimmed = link.trim();
    if (remote && trimmed && !/^https:\/\//i.test(trimmed)) {
      setError("The class link must start with https://");
      return;
    }
    setBusy(true);
    try {
      await api.patch(`/timetable/${slot.id}/`, {
        mode,
        meeting_link: remote ? trimmed : "",
        meeting_note: remote ? note.trim() : "",
      });
      navigation.goBack();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen keyboard>
      <Text style={type.label}>{slot.unit_code}</Text>
      <Text style={[type.title, { marginTop: space.xs }]}>{slot.unit_title}</Text>
      <Text style={[type.small, { marginTop: space.xs, marginBottom: space.xl }]}>
        {DAY_NAMES[slot.day]}, {clock(slot.start_time)} to {clock(slot.end_time)}
      </Text>

      <Banner message={error} />

      <Text style={[type.label, { marginBottom: space.sm }]}>How is this class held?</Text>
      <View style={{ flexDirection: "row", marginBottom: space.lg }}>
        <Chip label="In person" selected={mode === "in_person"} onPress={() => setMode("in_person")} />
        <Chip label="Online" selected={mode === "online"} onPress={() => setMode("online")} />
        <Chip label="Hybrid" selected={mode === "hybrid"} onPress={() => setMode("hybrid")} />
      </View>

      {remote ? (
        <>
          <TextField
            label="Class link"
            value={link}
            onChangeText={setLink}
            keyboardType="url"
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="https://"
            hint="Students registered for this unit will see a Join class button."
          />
          <TextField label="Passcode or instructions (optional)" value={note} onChangeText={setNote} maxLength={200} />
        </>
      ) : (
        <Text style={[type.small, { marginBottom: space.lg }]}>An in-person class has no link. Any link saved earlier is removed.</Text>
      )}

      <Button title="Save" onPress={save} loading={busy} />
    </Screen>
  );
}
