"""Original Vietnamese recording drafts, not historical quotations or game code.

Pairs are Vietnamese | English. Shared texts are instantiated per actor and age;
their reuse is recorded explicitly in VOICE_SCRIPTS.json. This file writes nothing.
"""

TEXTS = {}
def bank(key, text):
    rows = [tuple(s.strip() for s in line.split('|', 1)) for line in text.strip().splitlines() if line.strip()]
    assert len(rows) == 6, (key, len(rows))
    assert len({r[0] for r in rows}) == 6, key
    TEXTS[key] = rows

# Age-specific editorial choices. Modern orthography; all complete sentences are
# creative adaptations. These are register alternatives, not reconstructed IPA.
bank('select_A1', '''
Có tôi đây. | I am here.
Tôi nghe. | I am listening.
Gọi tôi chăng? | Were you calling me?
Cần gì nào? | What is needed?
Tôi đây. | Here I am.
Nói đi. | Speak.
''')
bank('select_A2', '''
Tôi đang nghe đây. | I am listening here.
Có việc gì? | What needs doing?
Tôi đã sẵn. | I am ready.
Xin cứ nói. | Please speak.
Cần tôi làm gì? | What shall I do?
Tôi chờ đây. | I am waiting here.
''')
bank('select_A3', '''
Đang chờ sai việc. | Awaiting a task.
Xin nghe lời dặn. | I am listening to the instructions.
Có việc, tôi xin làm. | If there is work, I will do it.
Đã có mặt. | Present.
Xin giao việc. | Give me a task.
Tôi đã chuẩn bị. | I have prepared.
''')
bank('select_A4', '''
Đã sẵn sàng nhận việc. | Ready to take a task.
Xin cho biết việc cần làm. | Tell me what needs doing.
Tôi đang chờ lệnh. | I am awaiting orders.
Cứ giao việc cho tôi. | Leave the task to me.
Tôi nghe rõ. | I hear clearly.
Đã đến, xin dặn việc. | I am here; give the instructions.
''')
bank('move_A1', '''
Đi đây. | Going.
Theo lối này. | This way.
Tôi tới đó. | I will go there.
Được, đi thôi. | Good, let us go.
Qua bên ấy. | Over that way.
Tôi theo. | I will follow.
''')
bank('move_A2', '''
Tôi đi ngay. | I will go at once.
Theo đường đã chỉ. | Along the indicated path.
Đến chỗ ấy thôi. | Let us go to that place.
Tôi sẽ tới. | I will get there.
Cứ theo tôi. | Follow me.
Chuyển sang bên kia. | Moving to the other side.
''')
bank('move_A3', '''
Theo lối đã định. | Following the chosen route.
Tôi lên đường. | I am setting off.
Đến nơi được chỉ. | Going to the indicated place.
Đã rõ đường đi. | The route is clear.
Tôi sẽ dẫn đường. | I will lead the way.
Đi, giữ bước cùng nhau. | Move, keep pace together.
''')
bank('move_A4', '''
Đang đi tới chỗ đã định. | Moving to the chosen position.
Theo đường này mà tiến. | Advance along this route.
Tôi nhận việc dẫn đường. | I will take the lead.
Đến đó ngay. | Going there now.
Đã rõ, bắt đầu đi. | Understood, setting out.
Giữ nhịp, cùng tiến lên. | Keep pace, advance together.
''')
bank('melee_A1', '''
Đánh thôi! | Strike!
Tới đây! | Come here!
Xông lên! | Charge!
Đừng lùi! | Do not fall back!
Đánh vào đó! | Strike there!
Theo ta! | Follow me!
''')
bank('melee_A2', '''
Cùng đánh tới! | Strike forward together!
Đừng để chúng qua! | Do not let them through!
Giữ chắc tay! | Keep a firm grip!
Tiến mà đánh! | Advance and strike!
Đánh sát vào! | Close in and strike!
Lên, cùng nhau! | Forward, together!
''')
bank('melee_A3', '''
Giữ hàng, đánh tới! | Keep ranks, strike forward!
Theo hiệu mà tiến! | Advance on the signal!
Chặn chúng ở đây! | Stop them here!
Đánh thẳng trước mặt! | Strike straight ahead!
Cùng giữ trận này! | Hold this fight together!
Tiến lên, đừng rời hàng! | Advance, keep ranks!
''')
bank('melee_A4', '''
Tiến đánh theo lệnh! | Advance and attack on orders!
Giữ đội ngũ, xông lên! | Keep formation, charge!
Cùng đánh vào chỗ ấy! | Strike that position together!
Chặn đường chúng lại! | Block their path!
Giữ vững rồi tiến! | Hold firm, then advance!
Theo cờ mà đánh! | Fight following the banner!
''')
bank('ranged_A1', '''
Bắn! | Shoot!
Nhắm cho chắc! | Take a steady aim!
Nhắm bên ấy! | Aim over there!
Đừng bắn vội! | Do not loose too soon!
Chờ chúng tới! | Wait for them to come!
Bắn vào đó! | Shoot there!
''')
bank('ranged_A2', '''
Cùng nhắm rồi bắn! | Aim together, then shoot!
Giữ tay cho vững! | Keep your hands steady!
Bắn đúng chỗ ấy! | Shoot at that spot!
Đợi hiệu rồi bắn! | Wait for the signal to shoot!
Chớ để lệch hướng! | Do not stray off aim!
Nhắm thẳng phía trước! | Aim straight ahead!
''')
bank('ranged_A3', '''
Theo hiệu, cùng bắn! | On the signal, shoot together!
Giữ hàng phía sau! | Keep the rear rank!
Nhắm nơi chúng tiến! | Aim where they advance!
Chọn đúng mục tiêu! | Choose the right target!
Đừng để chúng áp sát! | Do not let them close in!
Bắn, rồi giữ vị trí! | Shoot, then hold position!
''')
bank('ranged_A4', '''
Chờ hiệu lệnh, bắn! | Wait for the command, shoot!
Giữ đúng hướng bắn! | Keep the firing direction!
Cùng bắn vào mục tiêu! | Fire at the target together!
Nhắm kỹ trước khi bắn! | Aim carefully before shooting!
Giữ khoảng cách mà đánh! | Fight while keeping distance!
Bắn theo lệnh đã nhận! | Fire on the order received!
''')
bank('retreat_A1', '''
Lùi thôi! | Fall back!
Về phía này! | Back this way!
Rời chỗ ấy! | Leave that place!
Lùi lại mau! | Back, quickly!
Tránh ra! | Get clear!
Theo tôi về! | Follow me back!
''')
bank('retreat_A2', '''
Cùng lùi lại! | Fall back together!
Tránh đường chúng tới! | Get out of their path!
Tôi lui đây! | I am falling back!
Về chỗ an toàn! | Back to safety!
Rời nơi này thôi! | Let us leave here!
Mau theo lối cũ! | Quickly, along the old path!
''')
bank('retreat_A3', '''
Giữ hàng mà lui! | Withdraw in ranks!
Đưa nhau về sau! | Bring one another back!
Lui về chỗ đã định! | Withdraw to the chosen place!
Đừng rời người bên cạnh! | Stay with the person beside you!
Cùng về, giữ vững! | Back together, hold steady!
Rút khỏi chỗ hiểm! | Withdraw from danger!
''')
bank('retreat_A4', '''
Theo lệnh, lui quân! | Withdraw on orders!
Giữ đội ngũ khi lui! | Keep formation while withdrawing!
Rời trận địa này! | Leave this position!
Lui về tuyến sau! | Withdraw to the rear!
Đưa người bị thương về! | Bring the wounded back!
Cùng rút, chớ tản hàng! | Withdraw together, do not scatter!
''')

# These concrete task texts may be reused across chronological banks; no claim
# is made that more ornate synonyms would be more authentic. Re-record per bank.
bank('stop', '''
Dừng ở đây. | Stop here.
Tôi dừng lại. | I will stop.
Được, đứng lại. | Understood, stopping.
Không đi nữa. | No farther.
Giữ chỗ này. | Hold this place.
Tới đây là được. | This is far enough.
''')
bank('guard', '''
Tôi canh chỗ này. | I will watch this place.
Cứ để tôi trông. | Leave the watch to me.
Giữ mắt nhìn quanh. | Keep watch around us.
Tôi sẽ ở gần. | I will stay near.
Không để ai lọt qua. | Let no one slip past.
Tôi giữ phía này. | I will cover this side.
''')
bank('garrison', '''
Vào trong thôi. | Let us go inside.
Tôi vào trú. | I will take shelter inside.
Theo cửa này. | Through this entrance.
Tới chỗ có mái che. | To the shelter.
Vào giữ bên trong. | Go hold the interior.
Tôi tới cửa ngay. | I will go to the entrance now.
''')
bank('ungarrison', '''
Ra ngoài thôi. | Let us go outside.
Tôi ra ngay. | I will come out now.
Qua cửa rồi đi. | Through the entrance, then onward.
Rời chỗ trú. | Leaving shelter.
Tôi trở ra. | I am coming back out.
Cùng ra lối này. | Out this way together.
''')
bank('celebrate', '''
Được rồi! | We did it!
Qua được rồi! | We made it through!
Cùng nhau làm được! | We did it together!
Hôm nay tốt lắm! | A fine day!
Giữ vững như thế! | Keep it up!
May thay, đã xong! | Thankfully, it is done!
''')
bank('flee', '''
Tránh mau! | Get clear, quickly!
Chạy về đây! | Run back here!
Tìm chỗ nấp! | Find shelter!
Đừng đứng đó! | Do not stand there!
Qua lối này mau! | This way, quickly!
Rời chỗ nguy! | Leave the dangerous spot!
''')
bank('stealth', '''
Đi khẽ thôi. | Move quietly.
Giữ tiếng cho nhỏ. | Keep your voice low.
Theo bóng cây. | Follow the tree cover.
Chớ để lộ mình. | Do not reveal yourself.
Lặng mà tiến. | Advance silently.
Tôi sẽ giữ kín. | I will stay concealed.
''')
bank('ability_ack', '''
Đã rõ việc ấy. | That task is understood.
Tôi làm ngay đây. | I will do it now.
Chờ đúng lúc. | Wait for the right moment.
Cứ để tôi lo. | Leave it to me.
Theo cách đã định. | As planned.
Tôi đã sẵn tay. | I am ready to act.
''')
bank('farm', '''
Tôi ra đồng. | I will go to the fields.
Chăm ruộng cho tốt. | Tend the fields well.
Tới lúc làm ruộng. | Time to work the fields.
Tôi chăm chỗ lúa này. | I will tend this rice.
Cầm cuốc đi thôi. | Take the hoe and go.
Làm cho xong luống này. | Finish tending this strip.
''')
bank('forage', '''
Tôi hái quả. | I will gather fruit.
Gom quả vào giỏ. | Gather fruit into the basket.
Tìm quả chín thôi. | Look for ripe fruit.
Tôi hái ở đây. | I will gather here.
Chọn quả cho kỹ. | Choose the fruit carefully.
Mang giỏ tới nào. | Bring the basket.
''')
bank('hunt', '''
Tôi đi săn. | I am going hunting.
Theo dấu con mồi. | Follow the quarry's tracks.
Đến gần cho khẽ. | Approach quietly.
Tôi lấy thịt ở đây. | I will gather meat here.
Chuẩn bị săn thôi. | Prepare to hunt.
Đừng làm nó chạy. | Do not scare it away.
''')
bank('herd', '''
Đưa đàn về thôi. | Bring the herd back.
Theo tôi, về đây. | Follow me, back here.
Tôi trông đàn này. | I will watch this herd.
Chớ để đi lạc. | Do not let them stray.
Lùa về phía ấy. | Herd them that way.
Gom đàn lại nào. | Gather the herd.
''')
bank('wood', '''
Tôi đi đốn gỗ. | I will cut wood.
Chọn thân cây này. | Choose this trunk.
Mang rìu tới thôi. | Bring the axe.
Đốn rồi gom lại. | Cut it, then gather it.
Gỗ này dùng được. | This wood will do.
Tôi làm ở bìa rừng. | I will work at the forest edge.
''')
bank('gold', '''
Tôi đào vàng. | I will mine gold.
Lấy vàng từ quặng này. | Take gold from this ore.
Mang cuốc tới mỏ. | Bring the pick to the mine.
Gom vàng đem về. | Gather gold to bring back.
Tôi làm chỗ quặng này. | I will work this ore.
Tìm phần quặng tốt. | Find the good ore.
''')
bank('stone', '''
Tôi khai đá. | I will quarry stone.
Đục chỗ đá này. | Chisel this stone.
Chọn tảng cho chắc. | Choose a sound block.
Gom đá đem về. | Gather stone to bring back.
Mang búa đến đây. | Bring the hammer here.
Tôi làm ở mỏ đá. | I will work at the quarry.
''')
bank('build', '''
Tôi dựng nhà. | I will raise the building.
Đặt cột cho ngay. | Set the posts straight.
Mang gỗ tới đây. | Bring the timber here.
Cùng dựng cho chắc. | Raise it securely together.
Tôi bắt tay xây. | I will begin building.
Làm phần này trước. | Work on this part first.
''')
bank('repair', '''
Tôi sửa chỗ hỏng. | I will repair the damage.
Gia cố lại thôi. | Reinforce it.
Đưa vật liệu tới. | Bring the materials.
Làm cho vững lại. | Make it sound again.
Tôi vá chỗ này. | I will mend this part.
Còn sửa được đấy. | It can still be repaired.
''')
bank('carry', '''
Tôi mang về. | I will carry it back.
Gánh này đã đầy. | This load is full.
Đưa vào kho thôi. | Bring it to storage.
Tôi chuyển chỗ này. | I will move this load.
Mang về cho kịp. | Bring it back in time.
Để tôi gánh cho. | Let me carry it.
''')
bank('trade', '''
Tôi đưa hàng đi. | I will take the goods out.
Theo đường tới chợ. | Along the road to market.
Chuyến này sẽ tới nơi. | This shipment will get there.
Hàng đã chuẩn bị. | The goods are prepared.
Đi đổi hàng thôi. | Let us trade goods.
Giữ hàng cho cẩn thận. | Keep the goods safe.
''')
bank('trade_return', '''
Đưa hàng trở về. | Bring the goods back.
Chuyến buôn đã xong. | The trading trip is done.
Tôi trở về chợ. | I will return to market.
Hàng đã đổi được. | The goods have been traded.
Mang phần thu về. | Bring the proceeds back.
Tới lúc quay về. | Time to return.
''')
bank('tax', '''
Tôi đi thu thuế. | I will collect the tax.
Kiểm lại sổ thu. | Check the collection ledger.
Ghi đủ khoản này. | Record this amount fully.
Đem nộp vào kho. | Deliver it to the treasury.
Thu đúng phần đã định. | Collect the assessed portion.
Tôi nhận việc thu nộp. | I will handle the collection.
''')
bank('supervise', '''
Tôi trông việc ở đây. | I will oversee the work here.
Xem công việc tiến ra sao. | See how the work is progressing.
Làm cho đúng thứ tự. | Work in the proper order.
Tôi sẽ kiểm lại. | I will check it again.
Ghi rõ phần đã làm. | Record what has been done.
Cùng coi cho chu đáo. | Let us oversee it carefully.
''')
bank('heal', '''
Để tôi chăm sóc. | Let me tend to you.
Bình tâm, tôi tới đây. | Be calm, I am coming.
Hãy nghỉ một chút. | Rest a little.
Tôi giúp người bị thương. | I will help the wounded.
Cứ ngồi yên đây. | Stay still here.
Để tôi xem vết thương. | Let me see the wound.
''')
bank('relic', '''
Tôi giữ vật thiêng này. | I will care for this sacred object.
Mang về nơi an toàn. | Bring it somewhere safe.
Xin nâng cho cẩn thận. | Lift it carefully.
Tôi đưa về chùa. | I will take it to the monastery.
Giữ gìn cho nguyên vẹn. | Keep it intact.
Đưa vật này về thôi. | Let us bring this object back.
''')
bank('convert', '''
Xin hãy lắng nghe. | Please listen.
Hãy dừng tay lại. | Stay your hand.
Cùng tìm đường lành. | Let us seek a good path.
Bình tâm mà xét. | Consider with a calm mind.
Xin chớ gây thêm khổ. | Please cause no more suffering.
Hãy nghe lời tôi nói. | Hear what I have to say.
''')
bank('explore', '''
Tôi dò đường trước. | I will scout ahead.
Xem bên kia có gì. | See what lies beyond.
Tôi tìm lối qua. | I will find a way through.
Theo dấu đường mòn. | Follow the trail.
Tôi trông chừng từ xa. | I will watch from a distance.
Để tôi xem địa thế. | Let me survey the ground.
''')
bank('spear', '''
Giữ giáo phía trước! | Keep spears forward!
Chặn chúng bằng giáo! | Stop them with the spears!
Đâm cho chắc tay! | Thrust steadily!
Giữ mũi giáo thẳng! | Keep the spearpoints straight!
Cùng giữ hàng giáo! | Hold the spear rank together!
Chớ để chúng áp vào! | Do not let them press in!
''')
bank('sword', '''
Giữ chắc tay gươm! | Keep a firm sword grip!
Đánh sát vào chúng! | Close with them and strike!
Theo tôi, tiến đánh! | Follow me, advance and fight!
Giữ người bên cạnh! | Cover the one beside you!
Đánh rồi giữ thế! | Strike, then keep your stance!
Cùng giữ mũi tiến! | Hold the advance together!
''')
bank('bow', '''
Giương cung! | Draw the bows!
Lắp tên, chờ hiệu! | Nock, await the signal!
Buông dây! | Loose!
Nhắm kỹ mũi tên! | Aim the arrow carefully!
Giữ cung cho vững! | Hold the bow steady!
Cùng bắn tên tới! | Loose arrows together!
''')
bank('crossbow', '''
Nỏ đã sẵn! | The crossbow is ready!
Lắp tên vào nỏ! | Load the crossbow bolt!
Nhắm nỏ rồi bắn! | Aim the crossbow, then shoot!
Lên dây cho chắc! | Span it securely!
Chờ hiệu buông lẫy! | Wait for the release signal!
Giữ nỏ hướng ấy! | Keep the crossbow aimed there!
''')
bank('gun', '''
Giữ súng cho vững! | Hold the gun steady!
Nhắm rồi khai hỏa! | Aim, then fire!
Chờ lệnh mới bắn! | Wait for orders before firing!
Súng đã chuẩn bị! | The gun is prepared!
Giữ đúng hướng súng! | Keep the gun pointed correctly!
Cùng bắn theo hiệu! | Fire together on the signal!
''')
bank('horse_move', '''
Cho ngựa tiến lên. | Bring the horse forward.
Theo đường này, ngựa ơi. | This way, horse.
Tôi cưỡi tới đó. | I will ride there.
Giữ cương cho chắc. | Hold the reins firmly.
Qua chỗ đất tốt. | Over the sound ground.
Lên đường cùng nhau. | Let us ride out together.
''')
bank('horse_attack', '''
Theo tôi xông tới! | Charge with me!
Giữ ngựa thẳng hướng! | Keep the horse on course!
Cùng tiến đánh! | Advance and attack together!
Đánh rồi qua bên kia! | Strike, then ride through!
Theo hàng mà tiến! | Advance in line!
Giữ chắc cương, lên! | Hold the reins, forward!
''')
bank('elephant_move', '''
Cho voi tiến chậm. | Bring the elephant forward slowly.
Theo lối rộng này. | Along this wide path.
Giữ voi đi đều. | Keep the elephant moving steadily.
Đưa voi qua đó. | Bring the elephant across there.
Chờ nhau rồi tiến. | Wait for one another, then advance.
Tôi dẫn voi tới. | I will lead the elephant there.
''')
bank('elephant_attack', '''
Giữ voi hướng trước! | Keep the elephant facing forward!
Tiến đều mà đánh! | Advance steadily and fight!
Giữ vững trên lưng! | Keep steady on its back!
Cùng đánh từ đây! | Fight together from here!
Đừng để lệch hàng! | Do not drift from the line!
Theo hiệu, tiến lên! | On the signal, advance!
''')
bank('siege_move', '''
Cùng đẩy tới đó. | Push it there together.
Theo chỗ đất bằng. | Along the level ground.
Giữ bánh đi thẳng. | Keep the wheels straight.
Đưa máy tới nơi. | Bring the engine into position.
Chậm thôi, cùng đẩy. | Slowly, push together.
Giữ đều hai phía. | Keep both sides even.
''')
bank('siege_attack', '''
Nhắm đúng chỗ ấy! | Aim at that spot!
Máy đã sẵn, đánh! | The engine is ready, strike!
Giữ hướng rồi bắn! | Hold the aim, then shoot!
Cùng làm theo hiệu! | Work together on the signal!
Đánh vào mục tiêu! | Strike the target!
Giữ vị trí này! | Hold this position!
''')
bank('siege_deploy', '''
Đặt máy tại đây. | Set the engine here.
Giữ chân cho vững. | Secure its footing.
Chuẩn bị tại chỗ. | Prepare in position.
Cùng dựng bộ máy. | Set up the engine together.
Kiểm lại trước khi bắn. | Check it before shooting.
Đưa máy vào thế. | Bring the engine to readiness.
''')
bank('siege_pack', '''
Thu máy lại thôi. | Pack up the engine.
Chuẩn bị chuyển chỗ. | Prepare to move position.
Giữ các phần cho chắc. | Secure the parts.
Cùng thu dọn nào. | Pack it away together.
Tháo gọn rồi đi. | Pack it down, then move.
Đưa máy trở về. | Bring the engine back.
''')
bank('sail', '''
Đưa thuyền tới đó. | Bring the boat there.
Theo luồng nước này. | Follow this channel.
Giữ lái cho đều. | Keep a steady helm.
Theo luồng mà đi. | Go along the channel.
Chọn lối nước sâu. | Choose the deeper water.
Thuyền lên đường. | The boat is setting off.
''')
bank('naval_stop', '''
Giữ thuyền ở đây. | Hold the boat here.
Dừng thuyền lại. | Stop the boat.
Chờ ở khúc sông này. | Wait at this bend.
Giữ nguyên hướng lái. | Keep the present heading.
Chớ tiến thêm nữa. | Advance no farther.
Tôi giữ chỗ này. | I will hold this position.
''')
bank('fish', '''
Thả lưới thôi. | Cast the net.
Tìm đàn cá này. | Look for this shoal.
Kéo lưới cho đều. | Haul the net evenly.
Gom cá vào thuyền. | Gather the fish into the boat.
Tôi đánh cá ở đây. | I will fish here.
Giữ thuyền bên luồng cá. | Keep the boat by the fish.
''')
bank('naval_trade', '''
Đưa hàng tới bến. | Bring the cargo to the landing.
Theo dòng tới chợ. | Follow the river to market.
Hàng trên thuyền đã sẵn. | The cargo aboard is ready.
Giữ hàng khi qua sông. | Keep the cargo safe on the river.
Chuyến thuyền buôn lên đường. | The trading boat sets off.
Tôi tìm bến trao hàng. | I will find the trading landing.
''')
bank('naval_trade_return', '''
Thuyền quay về bến. | The boat returns to the landing.
Đưa hàng đã đổi về. | Bring the traded cargo back.
Theo luồng cũ trở về. | Return along the old channel.
Chuyến buôn xong, về thôi. | Trading done, let us return.
Giữ hàng cho tới bến. | Keep the cargo safe to the landing.
Tôi đưa thuyền về chợ. | I will take the boat back to market.
''')
bank('naval_attack', '''
Giữ mũi thuyền hướng ấy! | Keep the bow facing that way!
Theo luồng mà đánh! | Attack along the channel!
Chờ chúng vào tầm! | Wait for them to come into range!
Giữ lái, cùng đánh! | Hold the helm, attack together!
Chớ để thuyền mắc cạn! | Do not let the vessel run aground!
Nhắm đúng thuyền kia! | Aim at that vessel!
''')
bank('transport_load', '''
Lên thuyền lần lượt. | Board in order.
Giữ thuyền cho vững. | Keep the boat steady.
Đưa người qua đây. | Bring the people here.
Chờ mọi người lên đủ. | Wait until everyone is aboard.
Theo lối này lên thuyền. | Board this way.
Cùng chuẩn bị qua sông. | Prepare to cross together.
''')
bank('transport_unload', '''
Tới bờ, xuống thôi. | At the bank, disembark.
Lần lượt rời thuyền. | Leave the boat in order.
Đưa mọi người lên bờ. | Bring everyone ashore.
Giữ lái sát bến. | Hold the helm near the landing.
Qua lối này lên bãi. | This way onto the bank.
Chờ thuyền vững rồi xuống. | Wait until the boat is steady, then leave.
''')

ROLE_SELECT = {
'CIV_M': [('Tôi có mặt đây.', 'I am here.'), ('Có việc đồng áng chăng?', 'Is there fieldwork?'), ('Tay tôi còn rảnh.', 'My hands are free.'), ('Cứ gọi khi cần.', 'Call when needed.'), ('Dụng cụ đã sẵn.', 'The tools are ready.'), ('Tôi chờ việc mới.', 'I am waiting for new work.')],
'CIV_F': [('Tôi đang ở đây.', 'I am here.'), ('Cần người làm việc sao?', 'Do you need a worker?'), ('Tôi đã mang dụng cụ.', 'I have brought the tools.'), ('Có việc, cứ gọi tôi.', 'Call me if there is work.'), ('Tôi sẵn tay rồi.', 'My hands are ready.'), ('Việc gì tiếp đây?', 'What work comes next?')],
'SCOUT': [('Tôi đang dò đường.', 'I am scouting the route.'), ('Có lối nào cần xem?', 'Is there a route to inspect?'), ('Mắt tôi vẫn trông xa.', 'My eyes are watching afar.'), ('Tôi chờ hướng mới.', 'I am waiting for a new direction.'), ('Ngựa đã sẵn đường đi.', 'The horse is ready to travel.'), ('Để tôi nhìn phía trước.', 'Let me look ahead.')],
'INFANTRY': [('Hàng quân đã sẵn.', 'The rank is ready.'), ('Tôi giữ chỗ này.', 'I hold this place.'), ('Xin cho biết hướng đánh.', 'Give the direction of attack.'), ('Tay tôi đã vững.', 'My grip is steady.'), ('Tôi cùng hàng quân đây.', 'I am here with the rank.'), ('Chờ hiệu của người dẫn.', 'Awaiting the leader\'s signal.')],
'ARCHER': [('Cung tôi đã sẵn.', 'My bow is ready.'), ('Tên đã để gần tay.', 'The arrows are close at hand.'), ('Tôi nhìn rõ phía ấy.', 'I can see that direction.'), ('Chờ hiệu bắn tên.', 'Awaiting the signal to loose.'), ('Cung thủ có mặt.', 'Archer present.'), ('Tôi giữ chỗ bắn này.', 'I hold this shooting position.')],
'CROSSBOW': [('Nỏ đã lên dây.', 'The crossbow is spanned.'), ('Tôi đang chờ hiệu bắn.', 'I await the shooting signal.'), ('Tên nỏ đã chuẩn bị.', 'The bolts are prepared.'), ('Tôi giữ nỏ đây.', 'I am here with the crossbow.'), ('Có mục tiêu nào?', 'Is there a target?'), ('Nỏ thủ có mặt.', 'Crossbowman present.')],
'GUNNER': [('Súng đã sẵn sàng.', 'The gun is ready.'), ('Tôi giữ vị trí bắn.', 'I hold the firing position.'), ('Xin chỉ hướng súng.', 'Indicate where to aim the gun.'), ('Tôi chờ lệnh khai hỏa.', 'I await the command to fire.'), ('Người cầm súng có mặt.', 'Gunner present.'), ('Tôi đã kiểm lại súng.', 'I have checked the gun.')],
'CAVALRY': [('Ngựa đã sẵn.', 'The horse is ready.'), ('Tôi đang giữ cương.', 'I am holding the reins.'), ('Xin chỉ đường tiến.', 'Indicate the way forward.'), ('Người cưỡi ngựa có mặt.', 'Rider present.'), ('Tôi chờ hiệu lên đường.', 'I await the signal to ride.'), ('Hàng ngựa đã yên.', 'The mounted rank is steady.')],
'MONK': [('Tôi xin nghe.', 'I am listening.'), ('Có ai cần giúp?', 'Does anyone need help?'), ('Tôi đang ở đây.', 'I am here.'), ('Xin cứ bình tâm.', 'Please be at ease.'), ('Đường nào cần tới?', 'Which way should I go?'), ('Tôi sẵn lòng giúp.', 'I am willing to help.')],
'OFFICIAL': [('Sổ sách đã sẵn.', 'The ledgers are ready.'), ('Xin giao việc trông coi.', 'Give me the oversight task.'), ('Tôi chờ việc thu nộp.', 'I await collection duties.'), ('Kho nào cần kiểm?', 'Which store needs checking?'), ('Tôi đã có mặt.', 'I am present.'), ('Mọi khoản sẽ được ghi.', 'Every amount will be recorded.')],
'TRADER': [('Hàng đã xếp xong.', 'The goods are packed.'), ('Tôi chờ chuyến buôn.', 'I await a trading trip.'), ('Chợ nào cần tới?', 'Which market should I visit?'), ('Đường hàng đã sẵn.', 'The trading route is ready.'), ('Tôi trông hàng đây.', 'I am watching the goods.'), ('Có chuyến mới chăng?', 'Is there a new trip?')],
'ELEPHANT': [('Voi đã đứng yên.', 'The elephant is standing steady.'), ('Người dẫn voi có mặt.', 'Elephant handler present.'), ('Tôi giữ voi ở đây.', 'I hold the elephant here.'), ('Xin chỉ lối rộng.', 'Indicate a wide path.'), ('Trên lưng đã chuẩn bị.', 'Preparations aboard are complete.'), ('Tôi chờ hiệu tiến voi.', 'I await the signal to advance the elephant.')],
'SIEGE': [('Máy đã được kiểm.', 'The engine has been checked.'), ('Chúng tôi chờ vị trí.', 'We await a position.'), ('Đội máy có mặt.', 'Engine crew present.'), ('Xin chỉ chỗ đặt máy.', 'Indicate where to place the engine.'), ('Mọi người đã sẵn tay.', 'Everyone is ready.'), ('Tôi trông bộ máy này.', 'I am tending this engine.')],
'NAVAL_FISH': [('Thuyền cá đã sẵn.', 'The fishing boat is ready.'), ('Lưới đã để gần tay.', 'The net is close at hand.'), ('Tôi chờ luồng cá.', 'I await the fishing ground.'), ('Có chỗ đánh cá mới?', 'Is there a new fishing place?'), ('Tôi giữ thuyền đây.', 'I hold the boat here.'), ('Người đánh cá có mặt.', 'Fisher present.')],
'NAVAL_TRADE': [('Hàng trên thuyền đã đủ.', 'The cargo is all aboard.'), ('Tôi chờ bến đến.', 'I await the destination landing.'), ('Thuyền buôn đang đợi.', 'The trading boat is waiting.'), ('Xin cho biết bến hàng.', 'Name the cargo landing.'), ('Tôi trông hàng trên sông.', 'I watch the cargo on the river.'), ('Chuyến thuyền đã sẵn.', 'The voyage is ready.')],
'NAVAL_MILITARY': [('Thuyền chiến đã sẵn.', 'The war vessel is ready.'), ('Tôi đang giữ lái.', 'I am holding the helm.'), ('Xin chỉ hướng tiến thuyền.', 'Indicate the vessel\'s heading.'), ('Mọi người trên thuyền đã sẵn.', 'Everyone aboard is ready.'), ('Tôi chờ hiệu đánh.', 'I await the attack signal.'), ('Giữ thuyền tại đây.', 'Hold the vessel here.')],
}

for role, rows in ROLE_SELECT.items():
    assert len(rows) == len({x[0] for x in rows}) == 6, role

ROLE_SELECT['NAVAL_TRANSPORT'] = [
 ('Thuyền chở người đã sẵn.', 'The transport is ready.'),
 ('Tôi chờ người lên thuyền.', 'I await the passengers.'),
 ('Xin chỉ bờ bên kia.', 'Indicate the far bank.'),
 ('Lối lên thuyền đã thông.', 'The boarding way is clear.'),
 ('Tôi giữ thuyền gần bến.', 'I hold the boat near the landing.'),
 ('Cần đưa ai qua sông?', 'Who needs to cross the river?')]
ROLE_SELECT['NAVAL_FIRE'] = [
 ('Thuyền đã chuẩn bị.', 'The vessel is prepared.'),
 ('Tôi chờ hiệu tiến.', 'I await the signal to advance.'),
 ('Xin chỉ thuyền mục tiêu.', 'Indicate the target vessel.'),
 ('Giữ thuyền cách xa bạn quân.', 'Keep the vessel clear of allies.'),
 ('Tôi giữ hướng tiến này.', 'I hold this heading.'),
 ('Chờ đúng lúc mới tới.', 'Wait for the right moment to approach.')]

bank('under_attack', '''
Chúng đánh tới đây! | They are attacking here!
Có người đánh ta! | We are being attacked!
Cẩn thận phía ấy! | Watch that direction!
Giữ mình, chúng tới! | Take care, they are coming!
Đang bị đánh! | Under attack!
Đừng đứng lộ ra! | Do not stand exposed!
''')
bank('target_destroyed', '''
Mục tiêu đã hạ! | Target brought down!
Đã đánh xong chỗ ấy! | That target is dealt with!
Đã hạ được mục tiêu! | The target is brought down!
Xong rồi, giữ vững! | Done, hold steady!
Đã phá được! | It is destroyed!
Cùng giữ chỗ vừa lấy! | Hold the position just taken!
''')
bank('enemy_spotted', '''
Có quân phía trước! | Troops ahead!
Tôi thấy chúng rồi! | I see them!
Bên kia có địch! | Enemy on the far side!
Cẩn thận, có người tới! | Careful, someone is coming!
Quân địch đang tiến! | Enemy troops are advancing!
Tôi đã thấy bóng quân! | I have spotted troops!
''')
bank('formation', '''
Cùng giữ hàng nào. | Keep ranks together.
Đứng sát người bên cạnh. | Stand by the one beside you.
Theo hàng đã định. | Follow the chosen formation.
Chớ tách khỏi nhau. | Do not separate.
Giữ khoảng cách đều. | Keep even spacing.
Cùng đổi thế đứng. | Change formation together.
''')
bank('aim', '''
Giữ hướng nhắm! | Hold the aim!
Nhìn đúng mục tiêu! | Watch the target!
Tay vững, chờ hiệu! | Steady hands, await the signal!
Đợi chúng vào tầm! | Wait until they are in range!
Nhắm cho thật chắc! | Take a firm aim!
Chưa bắn, giữ nguyên! | Do not shoot yet, hold steady!
''')
bank('detonate', '''
Tới mục tiêu, châm lửa! | At the target, light it!
Giữ hướng, cho nổ! | Hold the heading, detonate!
Tránh xa, sắp nổ! | Stand clear, about to explode!
Theo hiệu, châm ngay! | On the signal, ignite!
Đã tới tầm, châm lửa! | In range, ignite!
Rời xa thuyền này! | Get clear of this vessel!
''')
bank('pickup_carcass', '''
Tôi mang con mồi về. | I will bring the quarry back.
Buộc cho chắc rồi đi. | Secure it, then go.
Đưa con mồi lên nào. | Lift the quarry aboard.
Tôi nhận chở phần này. | I will carry this part.
Nhấc lên cho cẩn thận. | Lift it carefully.
Mang về chỗ lấy thịt. | Bring it back for meat.
''')
bank('dropoff_carcass', '''
Đặt con mồi xuống đây. | Set the quarry down here.
Tôi đã đưa về. | I have brought it back.
Để gần chỗ làm thịt. | Leave it near the butchering place.
Tháo xuống cẩn thận. | Unload it carefully.
Con mồi đã tới nơi. | The quarry has arrived.
Tôi giao phần thịt này. | I am delivering this meat.
''')
bank('fish_dropoff', '''
Đưa cá lên bến. | Bring the fish to the landing.
Cá đã đầy thuyền. | The boat is full of fish.
Tôi mang cá về đây. | I am bringing the fish back here.
Gom cá cho gọn. | Gather the fish neatly.
Giao mẻ cá này. | Deliver this catch.
Tới bến, đưa cá xuống. | At the landing, unload the fish.
''')
bank('siege_ram', '''
Cùng đẩy vào đó! | Push into it together!
Đánh bật cổng này! | Break this gate!
Giữ máy đâm thẳng! | Keep the ram straight!
Theo nhịp mà đẩy! | Push in rhythm!
Đâm tiếp vào chỗ ấy! | Ram that spot again!
Cùng phá chỗ này! | Break this position together!
''')
bank('acknowledge', '''
Đã rõ. | Understood.
Tôi nhận việc. | I accept the task.
Được, tôi làm. | Good, I will do it.
Tôi đã nghe rõ. | I have heard clearly.
Sẽ làm theo lời dặn. | I will follow the instructions.
Việc ấy để tôi. | Leave that task to me.
''')
bank('marching_idle', '''
Cứ giữ đều bước. | Keep a steady pace.
Tôi vẫn trông đường. | I am still watching the path.
Cùng nhau đi tiếp. | Let us keep going together.
Giữ mắt nhìn phía trước. | Keep your eyes ahead.
Theo lối này mà đi. | Keep along this path.
Chớ để cách nhau xa. | Do not get too far apart.
''')
EFFORTS_EXTRA = {
 'fear_effort': [
   'Short startled gasp, no lexical warning.', 'Contained tremulous breath after a fright.',
   'Quick involuntary intake with a small nonverbal release.', 'Brief tense breath catch, no scream.',
   'Low startled grunt with immediate recovery.', 'Small shaken exhale, no spoken syllable.'],
 'incoming_effort': [
   'Instant ducking breath catch, no impact grunt.', 'Brief surprised intake at approaching danger.',
   'Sharp protective exhale, then silence.', 'Tiny nonverbal startled cry, comfortably supported.',
   'Low anticipatory grunt distinct from actual injury.', 'Sudden interrupted breath with a clean release.'],
 'warcry_effort': [
   'Short supported nonlexical rally cry, no historical slogan.', 'Low rising nonverbal call, compact release.',
   'Bright forward nonlexical shout, retain actor identity.', 'Clipped collective nonverbal call, not a chorus recording.',
   'Firm open-vowel exertion call without a Vietnamese word.', 'Brief forceful breath-led cry, no forced throat rasp.'],
 'cough_effort': [
   'One lightly acted dry cough, no forced irritation.', 'Small two-part simulated cough, natural recovery.',
   'Breathy cough-like exhale without throat strain.', 'Soft closed-mouth cough imitation, very short.',
   'Tiny interrupted exhale and clear recovery breath.', 'One low supported cough imitation, no illness claim.'],
 'healed_effort': [
   'Soft relieved exhale, no spoken thanks.', 'Small recovery intake then relaxed release.',
   'Brief nonverbal relief hum with easy breath.', 'Light breath settling after strain.',
   'Quiet relieved sigh, no magical sound design.', 'Short relaxed breath release, distinguish from pain.'],
 'inspired_effort': [
   'Short confident nonverbal breath-led call.', 'Brief uplifted nonlexical exhale, restrained.',
   'Quiet affirmative hum without a Vietnamese word.', 'Firm readiness breath with a clean stop.',
   'Small energized nonverbal grunt, not an attack.', 'Bright short nonlexical response, no sacred chant.'],
}

EFFORTS = {
 'pain_light': [
   'Short involuntary closed-mouth impact grunt; clean onset, no words.',
   'Brief caught breath after a glancing hit; recover without a spoken syllable.',
   'Quick breathy wince; small physical reaction, no theatrical scream.',
   'Low compressed impact exhale; keep the throat comfortable.',
   'Sharp intake followed by a small release; no lexical interjection.',
   'Tiny strained grunt then breath recovery; distinguish from attack effort.'],
 'pain_heavy': [
   'One forceful impact exhale and broken recovery breath; no words.',
   'Breath knocked out, brief strained groan; perform with safe support.',
   'Low involuntary groan with an abrupt catch; no sustained shout.',
   'Startled gasp then compressed exhale; severe impact, no acted diagnosis.',
   'Short rough nonverbal cry with breath release; avoid forced rasp.',
   'Interrupted breath and fading groan; distinct from a death performance.'],
 'death': [
   'Sudden lost breath followed by a short fading exhale; no final words.',
   'Soft involuntary gasp and release; no long melodramatic wail.',
   'Brief low collapse groan, then silence; do not add body impact sounds.',
   'Abrupt nonverbal cry cut into breath; comfortable vocal production.',
   'Small shocked intake followed by a weakening breath; no dialogue.',
   'Low broken exhale that falls away; no forced choking or throat compression.'],
 'exertion': [
   'Single supported lift exhale; compact and rhythmic.',
   'Two short push breaths, no words or animal imitation.',
   'Controlled pull grunt with clear release.',
   'Breathy working exhale, no deliberate lexical syllable.',
   'Short bracing grunt, then normal recovery breath.',
   'One sustained supported effort ending cleanly; no prop or weapon foley.'],
 'attack_effort': [
   'Short nonverbal striking exhale; separate from command dialogue.',
   'Compact thrust grunt with a clear breath release.',
   'Forceful supported exhale on a single effort; no shouted word.',
   'Quick breath catch and strike release; no weapon effect.',
   'Low attack grunt, brief enough not to mask the impact.',
   'Sharp nonverbal exertion burst; distinguish from being hit.'],
}
EFFORTS.update(EFFORTS_EXTRA)
