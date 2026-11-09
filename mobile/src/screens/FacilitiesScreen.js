import React, { useEffect, useMemo, useState } from "react";
import { ScrollView, Text, View } from "react-native";

import { Banner, Card, Chip, Empty, Loading, Screen, TextField } from "../components";
import { space, type } from "../theme";
import { useResource } from "../useResource";

export default function FacilitiesScreen() {
  const { data, error, loading, refreshing, refresh } = useResource("/facilities/");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState(null);
  const [needle, setNeedle] = useState("");

  // Wait for a pause in typing before filtering.
  useEffect(() => {
    const timer = setTimeout(() => setNeedle(query.trim().toLowerCase()), 200);
    return () => clearTimeout(timer);
  }, [query]);

  const categories = useMemo(() => {
    const seen = new Map();
    (data || []).forEach((f) => seen.set(f.category, f.category_label));
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [data]);

  const shown = (data || []).filter((f) => {
    if (category && f.category !== category) return false;
    if (!needle) return true;
    return [f.name, f.location, f.description].some((text) => String(text || "").toLowerCase().includes(needle));
  });

  if (loading && !data) return <Loading />;

  return (
    <Screen onRefresh={refresh} refreshing={refreshing}>
      <Banner message={error} />
      <TextField label="Search" value={query} onChangeText={setQuery} placeholder="Library, clinic, cafeteria" autoCorrect={false} style={{ marginBottom: space.md }} />
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: space.lg }}>
        <Chip label="All" selected={!category} onPress={() => setCategory(null)} />
        {categories.map((c) => (
          <Chip key={c.value} label={c.label} selected={category === c.value} onPress={() => setCategory(c.value)} />
        ))}
      </ScrollView>

      {shown.length === 0 ? <Empty title="No matches" message="Try a different search or category." /> : null}
      {shown.map((facility) => (
        <Card key={facility.id}>
          <Text style={type.label}>{facility.category_label}</Text>
          <Text style={[type.heading, { marginTop: space.xs }]}>{facility.name}</Text>
          {facility.description ? <Text style={[type.body, { marginTop: space.sm }]}>{facility.description}</Text> : null}
          <View style={{ marginTop: space.md }}>
            <Text style={type.small}>Where: {facility.location}</Text>
            {facility.opening_hours ? <Text style={type.small}>Hours: {facility.opening_hours}</Text> : null}
            {facility.contact ? <Text style={type.small}>Contact: {facility.contact}</Text> : null}
          </View>
        </Card>
      ))}
    </Screen>
  );
}
