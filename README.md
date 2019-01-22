# SubDomainBrute
子域名枚举工具，使用协程提高枚举速度。   
由于网上的工具不支持循环枚举子域名，所以有了此工具。  

## 功能
- 支持循环爆破  

## 安装说明
```
pip install dnspython gevent
```

## 使用说明
```
//默认使用循环枚举

python enum_domains.py -d qq.com

//指定字典
python enum_domains.py -f you_dict.txt -d qq.com

//关闭循环枚举
python enum_domains.py -n -d qq.com

//更多帮助
python enum_domains.py -h

```

## 后续功能
- 支持API搜索域名
- 支持域名监控

## 参考
- https://github.com/FeeiCN/ESD
- https://github.com/lijiejie/subDomainsBrute
- https://github.com/cvkki/src
