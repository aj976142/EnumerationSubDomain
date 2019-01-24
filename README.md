# SubDomainBrute
子域名枚举工具，使用协程提高枚举速度。   
由于网上的工具不支持循环枚举子域名，所以有了此工具。  

## 功能
- 支持循环枚举 
- 支持泛解析域名枚举
- 每次枚举的子域名自动加入精简字典

## 安装说明
```
pip install dnspython gevent requests
```

## 使用说明
```
//默认使用循环枚举

python enum_domains.py -d qq.com

//指定字典
python enum_domains.py -df you_dict.txt -d qq.com

//从文件中读取域名进行枚举
python enum_domains.py -f domains.txt

//关闭循环枚举
python enum_domains.py -n -d qq.com

//指定协程数和输出文件
python enum_domains.py -t 800 -d qq.com -o qq.com.txt

//泛解析的时候，很多域名是XX旗舰店的，可以用--filter过滤掉这些
python enum_domains.py -d jd.com -n --filter='旗舰店'

//更多帮助
python enum_domains.py -h

```
## 注意事项
协程数根据自己的带宽来设置，一般是200-800就够了，  
再高反而会有反作用，甚至因为过多的协程占满带宽，无法上网和正常枚举。

## 后续功能
- 支持API搜索域名
- 支持域名监控，发现新上线资产

## 参考
- https://github.com/FeeiCN/ESD
- https://github.com/lijiejie/subDomainsBrute
- https://github.com/cvkki/src
