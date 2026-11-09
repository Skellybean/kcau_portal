import React from "react";
import { Text, View } from "react-native";

import { useAuth } from "../auth/AuthContext";
import { Banner, Card, Empty, Loading, PageTitle, Screen, Tag } from "../components";
import { space, type } from "../theme";
import { useResource } from "../useResource";

export default function UnitsScreen({ navigation }) {
  const { user } = useAuth();
  const { data, error, loading, refreshing, refresh } = useResource("/units/?mine=1");

  if (loading && !data) return <Loading />;

  const subtitle =
    user.role === "student"
      ? "Registered on the KCA portal for this trimester"
      : user.role === "lecturer"
      ? "Units assigned to you"
      : "All units";

  return (
    <Screen top onRefresh={refresh} refreshing={refreshing}>
      <PageTitle title="Units" subtitle={subtitle} />
      <Banner message={error} />
      {data && data.length === 0 ? (
        <Empty
          title="No units yet"
          message={
            user.role === "student"
              ? "Units appear here after you register for them on the KCA portal. Pull down to refresh."
              : "No units are assigned to you yet."
          }
        />
      ) : null}
      {(data || []).map((unit) => (
        <Card key={unit.id} onPress={() => navigation.navigate("UnitDetail", { unit })} accessibilityLabel={`${unit.code} ${unit.title}`}>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
            <Text style={type.label}>{unit.code}</Text>
            <Tag>{unit.credits} credits</Tag>
          </View>
          <Text style={[type.heading, { marginTop: space.sm }]}>{unit.title}</Text>
          {unit.lecturer_name ? <Text style={[type.small, { marginTop: space.xs }]}>{unit.lecturer_name}</Text> : null}
        </Card>
      ))}
    </Screen>
  );
}
