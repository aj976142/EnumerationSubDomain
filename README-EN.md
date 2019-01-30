# EnumerationSubDomain
This tool was developed because online tools do not support circular enumeration of subdomains and monitoring of new subdomains.

## Features
- Support for loop enumeration(qq.com -> a.qq.com -> b.a.qq.com)
- Support for wildcard domain name enumeration(jd.com)
- Each sub-domain of the enumeration is automatically added to the condensed dictionary(mydict.txt)
- Support for domain name monitoring
- It supports automatic detection of DNS domain transfer Vulnerability
- Use coroutines to increase enumeration speed  

## Install
```
pip install dnspython gevent requests pyyaml
```

## Usage
Mail server configuration and filtering keywords should be configured in config.yaml


```
// Default closed loop enumeration, use the default dictionary(subdomains.txt)
python enum_domains.py -d qq.com


// Specify the dictionary to use when enumerating
python enum_domains.py -df you_dict.txt -d qq.com

// Using loop enumeration, because loop enumeration is a waste of time,
// after the first enumeration, loop enumeration defaults to using mydict.txt as a dictionary.
python enum_domains.py -l -d qq.com

// It is recommended to use the circular enumeration separately for this subdomain when looking for a vulnerability in a subdomain.
python enum_domains.py -l -d a.qq.com

// Specify a dictionary when looping enumerations
python enum_domains.py -l -ld yourdict.txt -d qq.com

// Close the filter, the filter keyword is configured in config.yaml
python enum_domains.py -nf -d qq.com


// Specify the number of associations, the default is 200
python enum_domains.py -t 100 -d qq.com

// Read the domain name from the file for enumeration
python enum_domains.py -f domains.txt


// Specify the number of associations and output files
python enum_domains.py -t 800 -d qq.com -o qq.com.txt

// Specify the time to start enumeration and send an email notification
// -e needs to configure the config.yaml file
// You need to enable the smtp function in the mailbox, and use -mf to specify the monitoring file. The monitoring file stores the domain name to be monitored.
// The domain name obtained this time will be written into the monitoring file every time.
// The result will be compared with the monitoring file to determine if there is a new domain name.
python enum_domains.py -d qq.com --start-time="02:00" -e -mf mointor.txt

// Non-monitoring mode to send email notification results
python enum_domains.py -d qq.com -n -e -mf qq_mointor.txt

// more help
python enum_domains.py -h

```
## Precautions
The number of associations is set according to your network bandwidth. If the domain name is not pan-resolved, setting 200-800 is enough.
Too many coroutines can be counterproductive, even because too many coroutines fill up the bandwidth, unable to access the Internet and normal enumeration.

Wildcard domain name enumeration is a waste of time.

## Future features
- Support API search domain name

## Reference
- https://github.com/FeeiCN/ESD
- https://github.com/lijiejie/subDomainsBrute
- https://github.com/cvkki/src
