"use client";

import AttendeePageLayout from "../../components/AttendeePageLayout";
import AttendeeDashboardView from "../../components/AttendeeDashboardView";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function Dashboard() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Attendee Dashboard" attendee={attendee}>
      {attendee.data && (
        <AttendeeDashboardView
          me={attendee.me}
          event={attendee.data.event}
          schedule={attendee.schedule}
        />
      )}
    </AttendeePageLayout>
  );
}
