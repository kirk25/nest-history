resource "google_compute_address" "nest_monitor" {
  name   = "nest-monitor-ip"
  region = "us-west1"
}

resource "google_compute_instance" "nest_monitor" {
  name         = "nest-monitor"
  machine_type = "e2-micro"
  zone         = "us-west1-b"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.nest_monitor.address
    }
  }

  tags = ["http-server", "https-server"]

  metadata = {
    ssh-keys = "kirk:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOPMZCOepcofrpAWSK3rZa7yAQ7JWpVQB+zJWc3pd19r kirk@nest-monitor"
  }

  service_account {
    email = "262126590832-compute@developer.gserviceaccount.com"
    scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring.write",
      "https://www.googleapis.com/auth/pubsub",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/trace.append",
    ]
  }
}
