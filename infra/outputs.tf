output "vm_external_ip" {
  value = google_compute_address.nest_monitor.address
}
