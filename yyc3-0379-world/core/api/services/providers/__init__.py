# file: __init__.py
# description: providers 协议转换层 - 每供应商一文件，协议变更只污染单文件
# author: YanYuCloudCube Team
# created: 2026-09-20
# status: active
# tags: [providers],[transform],[adapter]

"""providers/: 协议转换层（学 litellm ProviderConfig / one-api Adaptor）

新增供应商 = 新增一个实现 ProviderProtocol 的文件 + providers 注册表登记，路由器零改动。
"""
