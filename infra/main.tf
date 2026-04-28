terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "nest-thermostat-history-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = "nest-thermostat-history"
  region  = "us-west1"
  zone    = "us-west1-b"
}
