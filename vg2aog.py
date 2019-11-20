import json
from collections import Counter
with open("/home/dm/projects/VG2AOG/scene_graphs.json", 'r') as f:
    scene_graphs = json.loads(f.read())

print("open succeed")

AOG={}
choose_scene_name=["bedroom","living","kitchen","office","bathroom","dining","conference"]
for csn in choose_scene_name:

    ######################################################################
    ## 计算带有bedroom的imageid和统计存在bedroom的image中的object的数目
    ######################################################################
    count=0
    object_name=[]
    image_name=[]
    ob_id_name={}
    for image in scene_graphs:
        for object_id in image["objects"]:
            scene_name = object_id["names"][0]
            result = csn in scene_name
            # 若存在bedroom
            if result == True:
    #             print(object_id["names"][0])
                # 将图片id存入imagename
                image_name.append(image["image_id"]) 
                # 将每张image中的object存入subobject，并判断是否重复。即每张照片只保存object的一个（防止多个相同object在同一图像）
                subobject_name=[]
                for subobject_id in image["objects"]:
                    sub_result = csn in subobject_id["names"][0]
                    if subobject_id["names"][0] not in subobject_name \
                        and subobject_id["names"][0]!= "man" \
                        and subobject_id["names"][0]!= "woman" \
                        and subobject_id["names"][0]!= "wall" \
                        and sub_result==False:
                        subobject_name.append(subobject_id["names"][0]) 
                        object_name.append(subobject_id["names"][0]) 

                # 获取objectid到name的转换，为relationships做准备 
                for ob in image["objects"]:
                    ob_id_name[str(ob["object_id"])]=ob["names"][0]
                
                count=count+1
                break
    # 输出带有bedroom的图像数
    print(csn,count) 
    object_count=count
    # 计算集合object中每种object的数量
    recounted = Counter(object_name)
    # print(recounted) 
    # print(image_name)

    # 归一化object集合，即每种object的数目/带有bedroom的照片数量
    recounted_normalization={}
    for i in recounted:
        if recounted[i]/count > 0.1:
            recounted_normalization[i]=recounted[i]/object_count
    # print(recounted_normalization) 



    ######################################################################
    ## 计算属性概率
    ######################################################################
    count=0
    attribute_name=dict()
    for image in scene_graphs:
        # 只提取带有bedroom的图像中的目标的属性
        if image["image_id"] in image_name:
            for subobject_id in image["objects"]:
    #             print(subobject_id)
                #不是所有的object都带有attribute，需判断，否则报错
                if "attributes" in subobject_id:
                    for iterr in subobject_id["attributes"]:
    #                     print(type(subobject_id["attributes"]))
                        # 将属性存入对应的object，存入的是一个list，以方便扩充
                        if subobject_id["names"][0] in attribute_name:
                            attribute_name[subobject_id["names"][0]].append(iterr)
                        else:
                            attribute_name[subobject_id["names"][0]] = [iterr]
    #                     print(type(attribute_name[subobject_id["names"][0]]))
                
                count=count+1


    # print(count) 
    # # recounted = Counter(object_name)
    # print(attribute_name) 



    ######################################################################
    ## 计算每个object的属性的概率，即属性出现的次数/对应object的数目
    ######################################################################
    attribute_static={}
    attribute_p={}
    attr_p={}
    for a in attribute_name:
    #     print(a)
        attribute_static[a] = Counter(attribute_name[a])
        attribute_p[a] = Counter(attribute_name[a])
        for i in attribute_static[a]:
            if a in recounted:
    #             print(attribute_static[a][i])
    #             print(recounted[a])
                if attribute_static[a][i]/recounted[a]>0.1:
                    attribute_p[a][i] = attribute_static[a][i]/recounted[a]
                else :
                    del attribute_p[a][i]

        # 对于出现次数较少的object则不统计其属性概率，对于空list也不再添加
        if recounted[a]/object_count > 0.1 and attribute_p[a]:
            attr_p[a] = attribute_p[a]

    # print(attr_p)  




    ######################################################################
    ## 计算relationships概率
    ######################################################################
    # 定义关系dict
    relation={}
    subject_name = ''
    object_name = ''
    for image in scene_graphs:
        if image["image_id"] in image_name:
            for re in image["relationships"]:
                object_relation = {}
        #         print(re)
                # 求subject的id对应的name
                if str(re["subject_id"]) in ob_id_name:
                    subject_name = ob_id_name[str(re["subject_id"])]
        #             print("subject_id : ",ob_id_name[str(re["subject_id"])])
                else :
                    continue

                # 求objectid对应的name
                if str(re["object_id"]) in ob_id_name:
                    object_name = ob_id_name[str(re["object_id"])]
        #             print("object_id : ",ob_id_name[str(re["object_id"])])
                else :
                    continue

                # 将数据填充到object relationship
                object_relation[object_name] = [re["predicate"]]

                # 若之前无subject 则将其添加
                if subject_name not in relation:
                    relation[subject_name]=object_relation
        #             print(relation[subject_name])

                    continue

                # 若已有subject 则查找是否存在对应的object 没有则添加，有则在后面增加关系
                if object_name in relation[subject_name]:
        #             print(relation[subject_name][object_name])
                    relation[subject_name][object_name].append(re["predicate"])
        #             print(subject_name,object_name,re["predicate"])
        #             print(relation[subject_name][object_name])
                else :
                    relation[subject_name][object_name]=[re["predicate"]]
        #             print(" ",re["predicate"])



    ######################################################################
    ## 计算object的关系概率，即每种object与其他object的关系数量/该object的数量
    ######################################################################
    rela_p={}
    for rel in relation:
        # 复制relation的数据结构，如果不带.copy后面会改变relation的值
        rela_p[rel]=relation[rel].copy()
        
        relation_n={}
        for r in relation[rel]:  
            # 统计每种关系出现的次数，将list转为dict
            relation_n[r]=Counter(relation[rel][r])
    #         print(r)
            relation_p={}
            for rr in relation_n[r]:
                if rel in recounted and r in recounted and recounted[rel]/object_count > 0.1 and recounted[r]/object_count > 0.1:
                    if relation_n[r][rr]/recounted[rel]>0.05:
                        relation_p[rr]=relation_n[r][rr]/recounted[rel]
                    
    #        print(recounted[rel])

    #         if recounted[rel]/440 > 0.1:
    #             rela_p[rel][r]=relation_p[r][rr]
            if not relation_p:
                del rela_p[rel][r]
            else :
                Sum=0
                for rr in relation_p:
                    Sum=Sum+relation_p[rr]
                    if Sum>1:
                        Sum=0.9
                
                relation_p["sum"]=Sum
                rela_p[rel][r]=relation_p

                if Sum < 0.1:
                    del rela_p[rel][r]
            
        if not rela_p[rel]:
            del rela_p[rel]
        
    # print(recounted)
    # print(rela_p)
    # json_str = json.dumps(rela_p)
    # print(json_str)


    ######################################################################
    ## save all objects\attribute\relationships to file
    ######################################################################

    AOG_scene={}
    AOG_scene["objects"]=recounted_normalization
    AOG_scene["attribute"]=attr_p
    AOG_scene["relationships"]=rela_p
    AOG[csn]=AOG_scene
    # print(AOG)


with open("/home/dm/projects/VG2AOG/AOG_all.json", 'w') as f:
    json.dump(AOG,f)
    print("加载入文件完成...")