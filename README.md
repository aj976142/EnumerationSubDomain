# EnumerationSubDomain

[English README](/README-EN.md)

由于网上的工具不支持循环枚举子域名，以及监控新子域名，所以开发了此工具。  

## 功能
- 支持循环枚举(qq.com -> a.qq.com -> b.a.qq.com)
- 支持泛解析域名枚举(jd.com)
- 每次枚举的子域名自动加入精简字典(mydict.txt)
- 支持域名监控
- 支持自动检测DNS域传送漏洞
- 使用协程提高枚举速度   

## 安装说明
```
pip install dnspython gevent requests pyyaml
```

## 使用说明
邮件服务器配置和过滤关键词请在config.yaml中配置 


```
//默认关闭循环枚举(subdomains.txt)
python enum_domains.py -d qq.com

//指定枚举时使用的字典
python enum_domains.py -df you_dict.txt -d qq.com

//使用循环枚举, 由于循环枚举很浪费时间，在第一次枚举完后，循环枚举默认用mydict.txt作为字典
python enum_domains.py -l -d qq.com

//建议在找某个子域名的漏洞时，再对这个子域名单独使用循环枚举
python enum_domains.py -l -d a.qq.com

//指定循环枚举时的字典
python enum_domains.py -l -ld yourdict.txt -d qq.com

//关闭过滤器，过滤器关键词在config.yaml中配置
python enum_domains.py -nf -d qq.com


//指定协程数,默认为200,使用默认字典
python enum_domains.py -t 100 -d qq.com

//从文件中读取域名进行枚举
python enum_domains.py -f domains.txt


//指定协程数和输出文件
python enum_domains.py -t 800 -d qq.com -o qq.com.txt

//指定时间开始枚举并发送邮件通知，-e需要配置config.yaml文件，和--start-time配合使用
//并在邮箱中开启smtp功能， 同时使用-mf指定监控文件，监控文件存放要监控的域名
//每次运行都会把本次获取的域名写入监控文件，下次运行结果会和监控文件的比较，看是否有新域名
python enum_domains.py -d qq.com --start-time="02:00" -e -mf mointor.txt

//单独非监控模式发邮件通知结果
python enum_domains.py -d qq.com -n -e -mf qq_mointor.txt

//更多帮助
python enum_domains.py -h

```
## 注意事项
协程数根据自己的带宽来设置，非泛解析一般是200-800就够了,泛解析的协程数在20到100就够了
,再高反而会有反作用，甚至因为过多的协程占满带宽，无法上网和正常枚举。

泛解析的域名枚举会比较慢

## 后续功能
- 支持API搜索域名

## 参考
- https://github.com/FeeiCN/ESD
- https://github.com/lijiejie/subDomainsBrute
- https://github.com/cvkki/src
