terraform {
  required_providers {
    civo = {
      source  = "civo/civo"
      version = "~> 1.0"
    }
  }
}

# Object store credentials
resource "civo_object_store_credential" "bucket_creds" {
  name   = "${var.bucket_name}-creds"
  region = var.region
  
  access_key_id = var.access_key_id != "" ? var.access_key_id : null
}

# Object store bucket
resource "civo_object_store" "bucket" {
  name          = var.bucket_name
  region        = var.region
  max_size_gb   = var.max_size_gb
  access_key_id = civo_object_store_credential.bucket_creds.access_key_id
}




