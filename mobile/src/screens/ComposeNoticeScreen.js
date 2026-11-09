import React, { useState } from "react";
import { Switch, Text, View } from "react-native";

import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { Banner, Button, Chip, Screen, TextField } from "../components";
import { colors, space, type } from "../theme";

export default function ComposeNoticeScreen({ navigation }) {
  const { user } = useAuth();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [audience, setAudience] = useState("all");
  const [pinned, setPinned] = useState(false);
  const [errors, setErrors] = useState({});
  const [banner, setBanner] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    const next = {};
    if (!title.trim()) next.title = "Add a title.";
    if (!body.trim()) next.body = "Write the notice.";
    setErrors(next);
    setBanner(null);
    if (Object.keys(next).length) return;
    setBusy(true);
    try {
      await api.post("/announcements/", { title: title.trim(), body: body.trim(), audience, pinned: user.role === "admin" ? pinned : false });
      navigation.goBack();
    } catch (error) {
      setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen keyboard>
      <Banner message={banner} />
      <TextField label="Title" value={title} onChangeText={setTitle} error={errors.title} maxLength={200} />
      <TextField label="Message" value={body} onChangeText={setBody} error={errors.body} multiline numberOfLines={6} textAlignVertical="top" style={{ marginBottom: space.lg }} />

      <Text style={[type.label, { marginBottom: space.sm }]}>Send to</Text>
      <View style={{ flexDirection: "row", marginBottom: space.lg }}>
        <Chip label="Everyone" selected={audience === "all"} onPress={() => setAudience("all")} />
        <Chip label="Students" selected={audience === "students"} onPress={() => setAudience("students")} />
        <Chip label="Lecturers" selected={audience === "lecturers"} onPress={() => setAudience("lecturers")} />
      </View>

      {user.role === "admin" ? (
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: space.xl }}>
          <Text style={type.body}>Pin to the top</Text>
          <Switch value={pinned} onValueChange={setPinned} trackColor={{ true: colors.primary, false: colors.line }} thumbColor={colors.surface} />
        </View>
      ) : null}

      <Button title="Publish notice" onPress={submit} loading={busy} />
    </Screen>
  );
}
