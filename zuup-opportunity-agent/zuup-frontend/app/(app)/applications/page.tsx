// /applications redirects to /tracker (which IS the applications tracker)
import { redirect } from "next/navigation";

export default function ApplicationsRedirect() {
  redirect("/tracker");
}
