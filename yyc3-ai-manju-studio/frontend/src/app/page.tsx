import { redirect } from "next/navigation";

/** 根路径重定向到生产监控 */
export default function HomePage() {
  redirect("/production");
}
