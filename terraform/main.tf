module "codebuild" {
    source = "github.com/PeteTheAutomator/terraform-aws-codebuild"
    codebuild_project_name = "S3YumRepo"
    codebuild_project_description = "POC for S3 Yum Repo"
    codebuild_source_type = "GITHUB"
    codebuild_source_location = "https://github.com/PeteTheAutomator/AMIBuild.git"
    codebuild_image = "docker.io/petetheautomator/s3yumrepo"
    codebuild_vpc_id = "vpc-d1a64fb8"
    codebuild_subnets = ["subnet-5a2a3a21"]
    codebuild_security_group_ids = ["sg-902c74f8"]
}
