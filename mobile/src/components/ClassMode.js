import React from "react";
import { Alert, Linking, Text, View } from "react-native";

import { colors, space, type } from "../theme";
import { Button, Tag } from "./index";

// Only https links are ever opened, whatever the server sends.
export function isSafeLink(url) {
  return /^https:\/\//i.test(String(url || "").trim());
}

export async function openClassLink(url) {
  if (!isSafeLink(url)) {
    Alert.alert("Link not available", "This class link is not a secure https address, so it was not opened.");
    return;
  }
  try {
    await Linking.openURL(String(url).trim());
  } catch (error) {
    Alert.alert("Could not open the link", "Your phone could not open this link. Check that you have a browser or the meeting app installed.");
  }
}

export const MODE_LABEL = { in_person: "In person", online: "Online", hybrid: "Hybrid" };

// Where a class happens: the venue, an Online or Hybrid tag, and a Join button when there is a link.
// Pass onEdit to show the lecturer's "Edit class link" button.
export function ClassPlace({ slot, onEdit }) {
  const remote = slot.mode === "online" || slot.mode === "hybrid";
  return (
    <View style={{ marginTop: space.sm }}>
      <View style={{ flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: space.sm }}>
        {remote ? <Tag tone="accent">{MODE_LABEL[slot.mode]}</Tag> : null}
        {slot.venue ? <Text style={type.body}>{slot.venue}</Text> : null}
      </View>

      {remote && slot.meeting_link ? (
        <>
          <Button title="Join class" onPress={() => openClassLink(slot.meeting_link)} style={{ marginTop: space.md, minHeight: 44 }} />
          {slot.meeting_note ? (
            <Text selectable style={[type.small, { marginTop: space.sm }]}>
              {slot.meeting_note}
            </Text>
          ) : null}
        </>
      ) : null}
      {remote && !slot.meeting_link ? (
        <Text style={[type.small, { marginTop: space.sm, color: colors.muted }]}>The lecturer has not posted the class link yet.</Text>
      ) : null}

      {onEdit ? <Button title="Edit class link" variant="quiet" onPress={onEdit} style={{ marginTop: space.xs, minHeight: 40, alignSelf: "flex-start" }} /> : null}
    </View>
  );
}
