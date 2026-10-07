"use client";

import AttendeePageLayout from "../../../components/AttendeePageLayout";
import AttendeeBookingsView from "../../../components/AttendeeBookingsView";
import useAttendeeData from "../../../hooks/useAttendeeData";

export default function Interviews() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="My Schedule & Itinerary" attendee={attendee}>
      {attendee.data && <AttendeeBookingsView schedule={attendee.schedule} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
