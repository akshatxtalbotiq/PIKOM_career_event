"use client";

import AttendeeCheckInView from "../../components/AttendeeCheckInView";
import AttendeePageLayout from "../../components/AttendeePageLayout";
import useAttendeeData from "../../hooks/useAttendeeData";

export default function CheckIn() {
  const attendee = useAttendeeData();
  return (
    <AttendeePageLayout title="Check-in Pass" attendee={attendee}>
      {attendee.data && <AttendeeCheckInView checkin={attendee.checkin} />}
    </AttendeePageLayout>
  );
}
