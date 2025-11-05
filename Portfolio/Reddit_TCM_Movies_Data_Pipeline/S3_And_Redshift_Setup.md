# S3 bucket and Redshift cluster creation instructions

1. Create S3 bucket:

       $ aws s3api create-bucket --bucket my-reddit-tcm-movies-data-pipeline-project \
       --region us-west-2 \
       --create-bucket-configuration LocationConstraint=us-west-2

       {
           "Location": "http://my-reddit-tcm-movies-data-pipeline-project.s3.amazonaws.com/"
       }

2. Create IAM policy that has access to the ```my-reddit-tcm-movies-data-pipeline-project``` bucket:

       cat > policy.json << EOF
       {
           "Version":"2012-10-17",
           "Id": "FullAccessToRedditTCMMoviesBucket",
           "Statement": [
               {
                   "Sid": "FullAccessToRedditTCMMoviesBucket",
                   "Effect": "Allow",
                   "Action": [
                       "s3:GetObject",
                       "s3:GetBucketLocation",
                       "s3:ListBucket"
                   ],
                   "Resource": [
                       "arn:aws:s3:::my-reddit-tcm-movies-data-pipeline-project/*",
                       "arn:aws:s3:::my-reddit-tcm-movies-data-pipeline-project"
                   ]
               }
           ]
       }
       EOF


       $ aws iam create-policy \
           --policy-name FullAccessToRedditTCMMoviesBucket \
           --policy-document file://policy.json
       
       {
           "Policy": {
               "PolicyName": "FullAccessToRedditTCMMoviesBucket",
               "PolicyId": "ANPA2GVM57XOUXFZX4SVR",
               "Arn": "arn:aws:iam::111111111111:policy/FullAccessToRedditTCMMoviesBucket",
               "Path": "/",
               "DefaultVersionId": "v1",
               "AttachmentCount": 0,
               "PermissionsBoundaryUsageCount": 0,
               "IsAttachable": true,
               "CreateDate": "2025-10-23T20:41:26+00:00",
               "UpdateDate": "2025-10-23T20:41:26+00:00"
           }
       }

3. Create IAM Role that will be assumed by the Redshift cluster to access the bucket. Need to add ```redshift.amazonaws.com``` in the IAM policy that allows access to the bucket to allow Redshift to assume the Role:

       cat > assume-role-policy-document.json << EOF
       {
         "Version":"2012-10-17",
         "Statement": [
             {
                 "Effect": "Allow",
                 "Principal": {
                     "AWS": "arn:aws:iam::111111111111:root",
                     "Service": [
                         "redshift.amazonaws.com"
                     ]
                  },
                 "Action": "sts:AssumeRole"
             }
         ]
       }
       EOF


       $ aws iam create-role \
           --role-name FullAccessToRedditTCMMoviesBucket \
           --assume-role-policy-document file://assume-role-policy-document.json
       
       {
           "Role": {
               "Path": "/",
               "RoleName": "FullAccessToRedditTCMMoviesBucket",
               "RoleId": "AROA2GVM57XO5V6HJVLJC",
               "Arn": "arn:aws:iam::111111111111:role/FullAccessToRedditTCMMoviesBucket",
               "CreateDate": "2025-10-23T20:52:50+00:00",
               "AssumeRolePolicyDocument": {
                   "Version": "2012-10-17",
                   "Statement": [
                       {
                           "Effect": "Allow",
                           "Principal": {
                               "AWS": "arn:aws:iam::111111111111:root"
                           },
                           "Action": "sts:AssumeRole"
                       }
                   ]
               }
           }
       }
       
       
       $ aws iam attach-role-policy \
           --policy-arn arn:aws:iam::111111111111:policy/FullAccessToRedditTCMMoviesBucket \
           --role-name FullAccessToRedditTCMMoviesBucket

4. Create cluster:

       $ aws redshift create-cluster --db-name main \
           --cluster-identifier reddit-tcm-movies \
           --node-type ra3.large \
           --number-of-nodes 2 \
           --master-username root \
           --master-user-password hye5432%R%H \
           --iam-roles arn:aws:iam::111111111111:role/FullAccessToRedditTCMMoviesBucket \
           --publicly-accessible \
           --region us-west-2
       
       {
           "Cluster": {
               "ClusterIdentifier": "reddit-tcm-movies",
               "NodeType": "ra3.large",
               "ClusterStatus": "creating",
               "ClusterAvailabilityStatus": "Modifying",
               "MasterUsername": "my",
               "DBName": "main",
               "AutomatedSnapshotRetentionPeriod": 1,
               "ManualSnapshotRetentionPeriod": -1,
               "ClusterSecurityGroups": [],
               ...

5. Make sure Security Group in VPC used by the cluster allows access from the necessary IP(s).

       $ aws ec2 authorize-security-group-ingress \
           --group-id sg-0ab98aa6b05d2f609 \
           --ip-permissions 'IpProtocol=tcp,FromPort=5439,ToPort=5439,IpRanges=[{CidrIp=20.100.258.102/32}]'