# matchmeta

MatchMeta.Info project takes a list of AMIs owned by Amazon in the Oregon (US-WEST-2) region for x86_64 and arm64 architecture to collect investigation artifacts automatically.

AMI names that start with ```amazon/amzn``` and end with ```-gp2``` will be launched into a temporary VPC to collect the ```System.map``` file and run the ```getmeta``` collection script.

 - https://github.com/jblukach/getmeta

An archive of the SHA256 & MD5 hash lists plus System.map files to generate Volatility3 profiles for Amazon Linux are stored in this Github repository.

 - https://github.com/4n6ir/matchmeta.info

Also created a status page with RSS feed to know when AWS releases new AMIs, including a way to correlate matching IDs between regions.

 - https://matchmeta.4n6ir.com
