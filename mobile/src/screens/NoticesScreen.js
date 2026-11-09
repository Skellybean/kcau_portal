import React from "react";
import { Alert, Text, View } from "react-native";

import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { Banner, Button, Card, Empty, Loading, PageTitle, Screen, Tag } from "../components";
import { colors, space, type } from "../theme";
import { shortDate } from "../utils/format";
import { useResource } from "../useResource";

const AUDIENCE = { all: "Everyone", students: "Students", lecturers: "Lecturers" };

export default function NoticesScreen({ navigation }) {
  const { user } = useAuth();
  const { data, error, loading, refreshing, refresh, reload } = useResource("/announcements/");
  const canPost = user.role === "lecturer" || user.role === "admin";

  function confirmDelete(item) {
    Alert.alert("Delete notice", `Remove "${item.title}" for everyone?`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await api.del(`/announcements/${item.id}/`);
            reload();
          } catch (e) {
            Alert.alert("Could not delete", e.message);
          }
        },
      },
    ]);
  }

  if (loading && !data) return <Loading />;

  return (
    <Screen top onRefresh={refresh} refreshing={refreshing}>
      <PageTitle title="Notices" subtitle="Announcements from the university and your lecturers" />
      <Banner message={error} />
      {canPost ? <Button title="Post a notice" onPress={() => navigation.navigate("ComposeNotice")} style={{ marginBottom: space.lg }} /> : null}
      {data && data.length === 0 ? <Empty title="No notices" message="Nothing has been posted yet." /> : null}
      {(data || []).map((item) => (
        <Card key={item.id} style={item.pinned ? { borderLeftWidth: 3, borderLeftColor: colors.accent } : null}>
          <View style={{ flexDirection: "row", gap: space.sm, marginBottom: space.sm }}>
            {item.pinned ? <Tag tone="accent">Pinned</Tag> : null}
            <Tag>{AUDIENCE[item.audience]}</Tag>
          </View>
          <Text style={type.heading}>{item.title}</Text>
          <Text style={[type.body, { marginTop: space.sm }]}>{item.body}</Text>
          <Text style={[type.small, { marginTop: space.md, color: colors.muted }]}>
            {item.author_name ? `${item.author_name}, ` : ""}
            {shortDate(item.created_at)}
          </Text>
          {item.can_edit ? <Button title="Delete" variant="danger" onPress={() => confirmDelete(item)} style={{ marginTop: space.md, minHeight: 40 }} /> : null}
        </Card>
      ))}
    </Screen>
  );
}
