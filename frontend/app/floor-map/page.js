"use client";

import AttendeeFloorMapView from "../../components/AttendeeFloorMapView";
import AttendeePageLayout from "../../components/AttendeePageLayout";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function FloorMap() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Floor Map & Booths" attendee={attendee}>
      {attendee.data && <AttendeeFloorMapView floorMaps={attendee.data.floor_maps} />}
    </AttendeePageLayout>
  );
}
