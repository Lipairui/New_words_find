# New_words_find
Automatically extract words of a corpus.
## Example Usage
    sentences = ['小程序应该上个锁，让小朋友不能玩游戏。要不孩子天天就盯着玩','为什么微信小程序游戏点击会立刻闪退','加载小程序信息失败，无法起动',
                    '在小程序里很卡，总是死机','摇一摇摇到的怎么都是机器人','微信摇一摇摇到的人感觉都是假的，没人回也没动静','请解绑，摇一摇功能，谢谢',
                    '附近人摇一摇都加不上好友','无法正常试用微信摇一摇功能']
    result = new_words_find(sentences, min_freq=3, min_mtro=1, min_entro=0.5) 
    for res in result:
        print(res[0],res[1][0])
## Result
摇一摇 5      
小程序 4
            
