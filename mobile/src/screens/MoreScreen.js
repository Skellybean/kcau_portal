import React from "react";
import { Pressable, Text, View } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { PageTitle, Screen } from "../components";
import { colors, space, type } from "../theme";
import { roleLabel } from "../utils/format";

export default function MoreScreen({ navigation }) {
  const { user, signOut } = useAuth();

  const items = [
    { label: "Results", note: user.role === "student" ? "CAT, exam and grades" : "Results for your units", screen: "Results" },
    { label: "Campus directory", note: "Library, labs, clinic, food and services", screen: "Facilities" },
    { label: "Profile", note: `${roleLabel(user.role)}, ${user.email}`, screen: "Profile" },
  ];

  return (
    <Screen top>
      <PageTitle title="More" />
      {items.map((item) => (
        <Pressable
          key={item.label}
          onPress={() => navigation.navigate(item.screen)}
          accessibilityRole="button"
          style={({ pressed }) => [
            { paddingVertical: space.lg, borderBottomWidth: 1, borderBottomColor: colors.line },
            pressed && { opacity: 0.6 },
          ]}
        >
          <View>
            <Text style={type.heading}>{item.label}</Text>
            <Text style={[type.small, { marginTop: 2 }]} numberOfLines={1}>
              {item.note}
            </Text>
          </View>
        </Pressable>
      ))}
      <Pressable onPress={signOut} accessibilityRole="button" style={{ paddingVertical: space.lg }}>
        <Text style={[type.heading, { color: colors.danger }]}>Sign out</Text>
      </Pressable>
    </Screen>
  );
}
