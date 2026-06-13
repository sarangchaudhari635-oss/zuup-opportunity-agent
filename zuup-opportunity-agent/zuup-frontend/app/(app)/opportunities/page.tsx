// /opportunities redirects to /dashboard (which IS the opportunities feed)
import { redirect } from "next/navigation";

export default function OpportunitiesRedirect() {
  redirect("/dashboard");
}
