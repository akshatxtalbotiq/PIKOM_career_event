"use client";

import AttendeeBookingsView from "../../../components/AttendeeBookingsView";
import AttendeePageLayout from "../../../components/AttendeePageLayout";
import useAttendeeData from "../../../hooks/useAttendeeData";

export default function SavedJobs() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="My Schedule & Itinerary" attendee={attendee}>
      {attendee.data && <AttendeeBookingsView schedule={attendee.schedule} action={attendee.action} />}
    </AttendeePageLayout>
  );
}
