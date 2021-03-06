# Automate EBS Resize
## Introduction:
In this Article, we will go through step-by-step functionality of how to automatically increase the Size of EBS when it reaches its threshold.

If the AWS System Manager handles the Instances it becomes bit easier to resize the Volume and also modifying the file system to use the storage.

The following are the steps to follow to achieve the Target to Resize the EBS volume:
1. Set a Cloudwatch Alarm to Trigger when volume reaches its threshold.
2. Create an SNS Topic which will be triggered by cloudwatch Alarm.
3. SNS Topic in-return should trigger the Lambda function passing Instance-ID from cloudwatch alarm
4. Lambda function will call the Step function where the Process of EBS Resize is implemented.
5. Step Function: Check OS, Map the Volume, Take Snapshot, Modify EBS, Partitions the volume to be able to use the new size.

![Alt text](step_function.png?raw=true)

## Step-by-Step Explanation:
1. Set up Cloudwatch Alarm:  
	* Create an Instance(Windows/Linux)
	* Run Commands through System Manager, so the Instance is managed by SSM.
		* Commands to Run: AWS-ConfigureAWSPackage, AmazonCloudWatch-ManageAgent
	* Steps to Execute Command in SSM:
		* Create Parameter under System Manager, by providing the Name as “Config” and add value. Refer [This file](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/congif.txt)
		* Go to Run Command under System Manager, click on Run command Select AWS-ConfigureAWSPackage first from the list of predefined Packages.
		* Enter the Name as “AmazonCloudWatchAgent”, Version as “Latest”
		* Under “Targets” Select “Choose Instance Manually” and Select the Instance for which we would want to do the Automation.
		* Uncheck the Option to Enable S3 Bucket under “Output Options”. 
		* Click on Run. This will execute the Command.
	* Select AmazonCloudWatch-ManageAgent Second and follow the steps to Execute this command
		* Enter the “Optional Configuration Location” as “Config”, the parameter created in the parameter store.
		* Under “Targets” Select “Choose Instance Manually” and Select the Instance for which we would want to do the Automation.
		* Uncheck the Option to Enable S3 Bucket under “Output Options”. 
		* Click on Run. This will execute the Command.
	* Once both the Commands are executed Successfully we can Open the Cloudwatch Console. Create Alarm.
		* Select Metric-> Browse-> CW Agent-> ImageId, InstanceId, InstanceType, instance, objectname-> Select the Instance with LogicalDisk % Free Space Metric-> Select Metric.
		* All details pop up with a graphical representation of that Instance for the particular Metric.
		* Define the Condition based on your Requirement.Click Next.
		* Select an SNS Topic, which the Cloudwatch should Trigger. Will create SNS Topic in further Steps. Click Next
		* Set Alarm Name. Click Next, check the details and Click on Create Alarm. Alarm is successfully created and will trigger when it reaches the Condition set.

2. SNS Topic:
	* Open SNS Topic Console, Create Topic
	* Under the Topic Create Subscription, Protocol as AWS Lambda and Specify the Lambda Function to invoke in Endpoint.

3. Lambda Function to Invoke the Step-Function:
	* Open Lambda Console, Create Function
	* Enter the function Name, Select Python 3.9, create IAM Role with following policies and attach that role to all the Lambda Function. [Please follow this](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/IAM_Role.txt) document.
	* Click on Create Function, will redirect to the Function page with Basic Lambda Code, copy the below Lambda code and paste it in the console
	* This is the Lambda function which has been triggered by the SNS.
	* This Lambda code in return will trigger the Step function where all the steps for Modifying the EBS Resize will take place.
	* Environmental Variables passed- SSM_DOCUMENT_LINUX: “ssm_ebs_mapping_linux”, SSM_DOCUMENT_WINDOWS: “ssm_ebs_mapping_windows”, STATE_MACHINE_ARN:“arn:aws:states:us-east-2:826906654403:stateMachine:EBS_resize”
	* [Refer This File](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/Execution_state.py)

4. Step Function:
	* Check_OS:
		* This is Lambda code where the user identifies the OS of the Server(Instance) we are using to Resize.
		* Same IAM Role Policy is used here as well, as used in the above Lambda function.
		* Refer [This File](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/Check_OS.py).
		* The Input of this Lambda function will be 
		{
  		  "Instance_ID": "i-xxx",
  		  "SSM_Document_Name_Windows": "ssm_ebs_mapping_windows",
		  "SSM_Document_Name_Linux": "ssm_ebs_mapping_linux"
		}
		* The output of this Lambda function will be 
		{
  		  "Instance_ID": "i-xxx",
  		  "SSM_Document_Name_Windows": "ssm_ebs_mapping_windows",
  		  "SSM_Document_Name_Linux": "ssm_ebs_mapping_linux",
    		  "OS_Result": "windows"
		}
	* Choice State Over OS:
		* Check the Os of the Instance and Execute the Next step accordingly
	* SSM_GET_MAPPING:
		* This is a Lambda function, where the instance is mapped with the Volume ID, Drive Letter and Device
		* The code runs send_command to get the Details of the Volume. To execute send_command we need to have documents in SSM which we will discuss in the later part of the Article.
		* Refer [This File](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/Execute_SSM.py)
		* Input the function is passed from the check_OS lambda code
		{
  		  "Instance_ID": "i-048a40d07a753e961",
  		  "SSM_Document_Name_Windows": "ssm_ebs_mapping_windows",
  		  "SSM_Document_Name_Linux": "ssm_ebs_mapping_linux",
  		  "OS_Result": "windows"
		}
		* Output for the above function is:
		{
		  "Instance_ID": "i-xxx",
		  "SSM_Document_Name_Windows": "ssm_ebs_mapping_windows",
		  "SSM_Document_Name_Linux": "ssm_ebs_mapping_linux",
		  "OS_Result": "windows",
		  "SSM_Result": {
		    "Instance_ID": "i-xxx",
		    "Device": "/dev/sda1",
		    "EbsVolumeId": "vol-xxx",
		    "DriveLetter": "C"
		  }
		}
		* This Output is been passed to the next Lambda function, which is Modify_EBS

	* Modify_EBS:
		* This Lambda function modifies the Size of the Instance.
		* Refer [This Document for Code Snippet](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/Modify_EBS.py).
		* We define the Percentage Increase as Environment variable, INCREASE_PERCENTAGE: “0.1”
		* In this function, we also take a Snapshot of the Instance before Resizing it.
		* Output of the above code is:
		{
		  "Instance_ID": "i-xxx",
		  "SSM_Document_Name_Windows": "ssm_ebs_mapping_windows",
		  "SSM_Document_Name_Linux": "ssm_ebs_mapping_linux",
		  "OS_Result": "windows",
		  "SSM_Result": {
		    "Instance_ID": "i-xxx",
		    "Device": "/dev/sda1",
		    "EbsVolumeId": "vol-xxx",
		    "DriveLetter": "C"
		  },
		  "MODIFY_EBSResult": {
		    "SnapshotId": "snap-xxx",
		    "NewSize": 33
		  }
		}
		* EBS has been resized by 0.1% and New size is displayed in the output.
		* This Output is passed to the next Lambda function.

	* SSM_Partition:
		* Based on the OS it decides which state to execute, Windows/Linux
		* This Lambda function is used to partition the Volume to use the New Size.
		* This is the same code as SSM_MAPPING.Refer Excute_SSM.py for code snippet.

	* Publis_SNS:
		* This SNS is invoked when the volume of Instance Reaches 100GB.
  		* Create a SNS topic and Select Endpoint as your Mail ID, so you can receive mail when the Volume reaches 100 GB.

### Code Snippet for Step Function:
* Define proper function ARN for each Step.
* Refer [This document for Code Snippet](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/Step_Function.json).

### SYSTEM MANAGER:
* Open the System Manager Console, Go to Documents.
* Create two different Documents: ssm_ebs_mapping_windows, ssm_ebs_partition_windows
	* ssm_ebs_mapping_windows: This Document is created for all the OS, Linux/MAC/Windows. Used to Map the OS to the instance.
	* Refer [This Document for the text](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/ssm_ebs_mapping_windows.json).
	* ssm_ebs_partition_windows: This document is used to partition the New Size, so we can use it. This Document is particularly for Windows OS
	* Refer [This Document for the text](https://github.com/MehtaKajol/EBS_RESIZE/blob/main/ssm_ebs_partition_windows.json).

### Supporting Links:
* https://github.com/Road-To-FinOps-Deploy/aws_tf_ebs_resize 
* https://aws.amazon.com/blogs/storage/automating-amazon-ebs-volume-resizing-with-aws-step-functions-and-aws-systems-manager/

## Conclusion:
In this Article, we have seen how we can resize the EBS Volume automatically. Here we have seen end-to-end explanations on how each step is followed. 
The Error which we can face in the process is the “Execution Timed Out Error”, where we need to configure the time for each Lambda function. We can rely on this automation to automatically add additional EBS capacity as needed.
