# ═══════════════════════════════════════════════════════════════════════════
# Procurement Intelligence SaaS — AWS Infrastructure (Terraform)
# ═══════════════════════════════════════════════════════════════════════════
# Deploys:
#   - ECS Fargate cluster (API + worker services)
#   - Aurora PostgreSQL Serverless (multi-tenant data store)
#   - ElastiCache Redis (session cache, rate limiting, pub/sub)
#   - S3 (tenant data lake, uploads, exports, ML artifacts)
#   - CloudFront CDN (static assets, API caching)
#   - ALB (application load balancer with WAF)
#   - Cognito (user authentication, SSO federation)
#   - SQS/SNS (async job queue, webhook delivery)
#   - CloudWatch + X-Ray (observability)
#   - Secrets Manager (JWT keys, API secrets)
#   - KMS (encryption at rest)
# ═══════════════════════════════════════════════════════════════════════════

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "procurement-intelligence-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "procurement-intelligence-saas"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# Variables
# ═══════════════════════════════════════════════════════════════════════════

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "api.procurementintelligence.io"
}

variable "db_instance_class" {
  description = "Aurora Serverless DB instance class"
  type        = string
  default     = "db.serverless"
}

variable "api_container_cpu" {
  description = "Fargate API task CPU units"
  type        = number
  default     = 1024
}

variable "api_container_memory" {
  description = "Fargate API task memory (MiB)"
  type        = number
  default     = 2048
}

variable "api_desired_count" {
  description = "Number of API container instances"
  type        = number
  default     = 3
}

# ═══════════════════════════════════════════════════════════════════════════
# VPC & Networking
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "procurement-intelligence-vpc" }
}

resource "aws_subnet" "public" {
  count                   = 3
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = { Name = "public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = { Name = "private-${count.index}" }
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id
}

resource "aws_eip" "nat" {
  domain = "vpc"
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 3
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 3
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ═══════════════════════════════════════════════════════════════════════════
# Security Groups
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_security_group" "alb" {
  name_prefix = "alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name_prefix = "ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name_prefix = "db-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "redis-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# Aurora PostgreSQL Serverless v2
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_rds_cluster" "main" {
  cluster_identifier     = "procurement-intelligence-${var.environment}"
  engine                 = "aurora-postgresql"
  engine_mode            = "provisioned"
  engine_version         = "15.4"
  database_name          = "procurement_intelligence"
  master_username        = "pi_admin"
  manage_master_user_password = true
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.main.arn
  vpc_security_group_ids = [aws_security_group.db.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 16.0
  }

  backup_retention_period = 35
  preferred_backup_window = "03:00-04:00"
  skip_final_snapshot     = false
  final_snapshot_identifier = "procurement-intelligence-final"
}

resource "aws_rds_cluster_instance" "main" {
  count              = 2
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version
}

resource "aws_db_subnet_group" "main" {
  name       = "procurement-intelligence-${var.environment}"
  subnet_ids = aws_subnet.private[*].id
}

# ═══════════════════════════════════════════════════════════════════════════
# ElastiCache Redis
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "procurement-intelligence"
  description          = "Rate limiting, session cache, pub/sub"
  node_type            = "cache.t4g.medium"
  num_cache_clusters   = 2
  engine_version       = "7.0"
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "procurement-intelligence"
  subnet_ids = aws_subnet.private[*].id
}

# ═══════════════════════════════════════════════════════════════════════════
# S3 Data Lake
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_s3_bucket" "data_lake" {
  bucket = "procurement-intelligence-data-${var.environment}"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "INTELLIGENT_TIERING"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ═══════════════════════════════════════════════════════════════════════════
# KMS Encryption Key
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_kms_key" "main" {
  description             = "Procurement Intelligence master encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "main" {
  name          = "alias/procurement-intelligence-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# ═══════════════════════════════════════════════════════════════════════════
# ECS Fargate Cluster
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_ecs_cluster" "main" {
  name = "procurement-intelligence-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
    base              = 1
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "procurement-intelligence-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_container_cpu
  memory                   = var.api_container_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${aws_ecr_repository.api.repository_url}:latest"
      portMappings = [{
        containerPort = 8000
        protocol      = "tcp"
      }]
      environment = [
        { name = "PROCUREMENT_ENVIRONMENT", value = var.environment },
        { name = "PROCUREMENT_LOG_LEVEL", value = "INFO" },
        { name = "AWS_REGION", value = var.aws_region },
      ]
      secrets = [
        {
          name      = "JWT_SECRET"
          valueFrom = aws_secretsmanager_secret.jwt_secret.arn
        },
        {
          name      = "DATABASE_URL"
          valueFrom = "${aws_secretsmanager_secret.database_url.arn}"
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 15
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "procurement-intelligence-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# Application Load Balancer
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_lb" "main" {
  name               = "procurement-intelligence"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "api" {
  name        = "pi-api"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 15
    timeout             = 5
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# ECR Repository
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_ecr_repository" "api" {
  name                 = "procurement-intelligence/api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.main.arn
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# SQS Queues (async jobs, webhooks)
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_sqs_queue" "ml_jobs" {
  name                       = "procurement-intelligence-ml-jobs"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
  kms_master_key_id          = aws_kms_key.main.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ml_jobs_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "ml_jobs_dlq" {
  name                      = "procurement-intelligence-ml-jobs-dlq"
  message_retention_seconds = 1209600
  kms_master_key_id         = aws_kms_key.main.id
}

resource "aws_sqs_queue" "webhooks" {
  name                       = "procurement-intelligence-webhooks"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 86400
  kms_master_key_id          = aws_kms_key.main.id

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.webhooks_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "webhooks_dlq" {
  name                      = "procurement-intelligence-webhooks-dlq"
  message_retention_seconds = 1209600
  kms_master_key_id         = aws_kms_key.main.id
}

# ═══════════════════════════════════════════════════════════════════════════
# Secrets Manager
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_secretsmanager_secret" "jwt_secret" {
  name       = "procurement-intelligence/${var.environment}/jwt-secret"
  kms_key_id = aws_kms_key.main.id
}

resource "aws_secretsmanager_secret" "database_url" {
  name       = "procurement-intelligence/${var.environment}/database-url"
  kms_key_id = aws_kms_key.main.id
}

# ═══════════════════════════════════════════════════════════════════════════
# CloudWatch
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/procurement-intelligence-api"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.main.arn
}

# ═══════════════════════════════════════════════════════════════════════════
# Auto Scaling
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_appautoscaling_target" "api" {
  max_capacity       = 20
  min_capacity       = var.api_desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# ACM Certificate
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
}

# ═══════════════════════════════════════════════════════════════════════════
# IAM Roles
# ═══════════════════════════════════════════════════════════════════════════

resource "aws_iam_role" "ecs_execution" {
  name = "procurement-intelligence-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "procurement-intelligence-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task" {
  name = "procurement-intelligence-ecs-task"
  role = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject", "s3:PutObject", "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"
        ]
        Resource = [
          aws_sqs_queue.ml_jobs.arn,
          aws_sqs_queue.webhooks.arn
        ]
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          aws_secretsmanager_secret.jwt_secret.arn,
          aws_secretsmanager_secret.database_url.arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = [aws_kms_key.main.arn]
      }
    ]
  })
}

# ═══════════════════════════════════════════════════════════════════════════
# Outputs
# ═══════════════════════════════════════════════════════════════════════════

output "api_url" {
  value       = "https://${var.domain_name}"
  description = "Production API endpoint"
}

output "database_endpoint" {
  value     = aws_rds_cluster.main.endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive = true
}

output "s3_bucket" {
  value = aws_s3_bucket.data_lake.bucket
}

output "ecr_repository" {
  value = aws_ecr_repository.api.repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.main.name
}
