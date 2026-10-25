"""Age-sensitive editorial alternatives, not attested historical commands.

The shared bank is A2 for these task pools. A1 emphasizes immediate concrete
action; A3 coordination; A4 practiced occupational phrasing. These choices do
not assign first-attestation dates to any word or replace historical review.
"""
AGE_TEXTS={}
def add(key,age,text):
    rows=[tuple(s.strip() for s in l.split('|',1)) for l in text.strip().splitlines() if l.strip()]
    assert len(rows)==len({r[0] for r in rows})==6,(key,age)
    AGE_TEXTS[(key,age)]=rows

add('farm','A1','''
Ra ruộng thôi. | To the fields.
Tôi cuốc đất đây. | I will hoe the soil here.
Chăm cây lúa này. | Tend this rice plant.
Làm ở luống này. | Work this strip.
Tới đồng, làm thôi. | To the fields, let us work.
Giữ cho lúa tốt. | Keep the rice healthy.
''')
add('farm','A3','''
Cùng chăm ruộng này. | Tend this field together.
Chia nhau làm từng luống. | Divide the strips between us.
Tôi nhận việc đồng áng. | I will take the fieldwork.
Giữ cây lúa cho đều. | Keep the rice growing evenly.
Làm ruộng cho kịp vụ. | Work the fields in season.
Tôi chăm phần ruộng ấy. | I will tend that part of the field.
''')
add('farm','A4','''
Tôi sẽ coi việc ruộng này. | I will tend this field's work.
Lúa đang cần người chăm. | The rice needs tending.
Tới đồng làm cho kịp. | To the fields, work in time.
Tôi nhận phần làm ruộng. | I will take a share of the fieldwork.
Chăm từng luống cho tốt. | Tend each strip well.
Việc đồng này để tôi. | Leave this fieldwork to me.
''')
add('wood','A1','''
Đốn cây này thôi. | Cut this tree.
Rìu ở tay rồi. | The axe is in hand.
Tôi lấy gỗ đây. | I will get wood here.
Chọn cây mà đốn. | Choose a tree to cut.
Mang gỗ về thôi. | Bring the wood back.
Tôi tới chỗ cây ấy. | I will go to that tree.
''')
add('wood','A3','''
Cùng đốn lấy gỗ. | Cut wood together.
Chọn cây cho đúng việc. | Choose timber for the task.
Tôi nhận phần đốn cây. | I will take the tree cutting.
Đốn xong, gom một chỗ. | After cutting, gather it together.
Tôi tới bìa rừng làm. | I will work at the forest edge.
Gỗ lấy về dùng chung. | Bring the timber back for use together.
''')
add('wood','A4','''
Tôi sẽ lo phần gỗ. | I will handle the timber.
Đốn cây theo chỗ đã chỉ. | Cut at the indicated place.
Gom gỗ đủ cho công việc. | Gather enough timber for the work.
Mang rìu, bắt đầu đốn. | Take the axe, begin cutting.
Tôi nhận việc lấy gỗ. | I will take the wood gathering.
Chọn thân gỗ dùng được. | Choose a usable trunk.
''')
add('build','A1','''
Dựng lên thôi. | Raise it.
Tôi đặt cột đây. | I will place the post here.
Gỗ mang tới rồi. | The timber has arrived.
Làm nền trước thôi. | Work on the foundation first.
Giữ cho đứng vững. | Keep it standing firmly.
Tôi bắt đầu dựng. | I am beginning to build.
''')
add('build','A3','''
Cùng đặt nền cho chắc. | Set a firm foundation together.
Chia nhau dựng từng phần. | Divide the building work between us.
Giữ hàng cột cho ngay. | Keep the row of posts straight.
Gom đủ gỗ rồi dựng. | Gather enough timber, then build.
Tôi nhận phần xây này. | I will take this building work.
Theo chỗ đã định mà xây. | Build at the chosen place.
''')
add('build','A4','''
Tôi sẽ coi phần dựng này. | I will handle this part of the building.
Đặt nền theo chỗ đã chỉ. | Lay the foundation as indicated.
Kiểm cột trước khi dựng tiếp. | Check the posts before building on.
Vật liệu đã có, xây thôi. | The materials are here, let us build.
Cùng hoàn thành phần này. | Finish this part together.
Tôi nhận việc xây dựng. | I will take the construction work.
''')
add('trade','A1','''
Mang hàng đi thôi. | Take the goods out.
Tôi tới chỗ đổi hàng. | I will go to the trading place.
Hàng buộc chắc rồi. | The goods are secured.
Theo đường tới đó. | Along the road there.
Tôi đem phần hàng này. | I will take these goods.
Đi một chuyến nào. | Let us make a trip.
''')
add('trade','A3','''
Cùng đưa hàng tới chợ. | Bring the goods to market together.
Tôi nhận chuyến hàng này. | I will take this shipment.
Giữ đường hàng cho thông. | Keep the trading route clear.
Đổi hàng rồi trở về. | Trade the goods, then return.
Hàng đã đủ, lên đường. | The goods are ready, set off.
Tôi tới nơi trao hàng. | I will go to the trading place.
''')
add('trade','A4','''
Chuyến buôn đã chuẩn bị xong. | The trading trip is prepared.
Tôi sẽ đưa hàng tới chợ. | I will take the goods to market.
Đem hàng theo đường đã định. | Take the goods along the chosen route.
Giữ hàng nguyên vẹn tới nơi. | Keep the goods intact to the destination.
Tôi nhận việc trao đổi này. | I will handle this trade.
Tới chợ, làm cho xong chuyến. | To market, finish the trip.
''')
add('heal','A1','''
Để tôi giúp. | Let me help.
Ngồi yên ở đây. | Stay still here.
Tôi xem chỗ đau. | I will look at the hurt.
Nghỉ tay một chút. | Rest a little.
Tôi tới gần đây. | I am coming close.
Bình tâm, có tôi. | Be calm, I am here.
''')
add('heal','A3','''
Cùng chăm người bị thương. | Tend the wounded together.
Để tôi xem cho kỹ. | Let me look carefully.
Xin nghỉ ở chỗ này. | Rest at this place.
Tôi nhận việc chăm sóc. | I will take the care work.
Bình tâm, đừng vội đi. | Be calm, do not hurry away.
Để người bị thương được nghỉ. | Let the wounded rest.
''')
add('heal','A4','''
Tôi sẽ chăm vết thương này. | I will tend this wound.
Xin ngồi yên để tôi xem. | Stay still so I can look.
Đưa người bị thương tới đây. | Bring the wounded here.
Tôi nhận việc giúp người này. | I will take care of this person.
Hãy nghỉ, tôi đang tới. | Rest, I am coming.
Chăm sóc cho người đỡ khổ. | Care for them to ease their suffering.
''')
add('tax','A1','''
Tôi thu phần này. | I will collect this portion.
Gom đủ rồi nộp. | Gather the amount, then deliver it.
Đếm cho đúng thôi. | Count it correctly.
Tôi mang phần thu về. | I will bring the collection back.
Ghi lại khoản ấy. | Record that amount.
Đưa vào kho đây. | Bring it to this store.
''')
add('tax','A3','''
Kiểm đủ phần phải nộp. | Check the assessed portion.
Tôi nhận việc thu thuế. | I will take the tax collection.
Ghi từng khoản vào sổ. | Enter each amount in the ledger.
Đếm lại rồi đem nộp. | Count again, then deliver it.
Thu đúng, chớ thu thừa. | Collect correctly, not in excess.
Tôi đưa phần thu về kho. | I will bring the collection to the treasury.
''')
add('tax','A4','''
Sổ thu đã mở, tôi đi. | The collection ledger is open; I am going.
Kiểm khoản thu theo sổ. | Check the collection against the ledger.
Tôi sẽ lo việc thu nộp. | I will handle collection and delivery.
Ghi rõ số đã nhận. | Record the amount received clearly.
Đưa phần thu tới đúng kho. | Deliver the collection to the right treasury.
Thu nộp theo phần đã định. | Collect and deliver the assessed portion.
''')
add('bow','A1','''
Kéo cung lên! | Draw the bow!
Đặt tên đây! | Nock the arrow!
Buông tên thôi! | Loose the arrow!
Nhắm bằng cung này! | Aim with this bow!
Giữ chắc dây cung! | Hold the bowstring firmly!
Bắn tên tới! | Shoot the arrow forward!
''')
add('bow','A3','''
Cung cùng giương, chờ hiệu! | Bows drawn together, await the signal!
Đặt tên rồi giữ hàng! | Nock, then keep ranks!
Theo hiệu, buông tên! | On the signal, loose arrows!
Giữ cung hướng phía trước! | Keep bows facing forward!
Chớ rời hàng cung thủ! | Stay in the archers' rank!
Cùng nhắm nơi chúng tiến! | Aim together where they advance!
''')
add('bow','A4','''
Cung thủ, chờ lệnh bắn! | Archers, await the firing order!
Giữ cung vững trước khi buông! | Steady the bow before loosing!
Cùng bắn tên theo hiệu lệnh! | Loose arrows together on command!
Lắp tên, nhắm đúng mục tiêu! | Nock, aim at the target!
Đừng để dây cung trượt tay! | Do not let the string slip!
Theo cờ mà giữ hướng bắn! | Follow the banner's firing direction!
''')
add('crossbow','A1','''
Giữ nỏ đây! | Hold the crossbow here!
Lấy tên nỏ! | Take the bolt!
Đưa nỏ lên! | Raise the crossbow!
Kéo dây nỏ thôi! | Span the crossbow!
Bắn bằng nỏ này! | Shoot with this crossbow!
Nhắm nỏ vào đó! | Aim the crossbow there!
''')
add('crossbow','A3','''
Nỏ cùng lên dây! | Span the crossbows together!
Chờ hiệu rồi buông lẫy! | Wait for the signal, then release!
Giữ hàng nỏ phía này! | Keep the crossbow rank this side!
Lắp tên xong, cùng nhắm! | Bolts loaded, aim together!
Chớ để nỏ lệch hướng! | Do not let the crossbow drift off aim!
Theo hiệu mà bắn nỏ! | Shoot the crossbows on the signal!
''')
add('crossbow','A4','''
Nỏ thủ, chuẩn bị bắn! | Crossbowmen, prepare to shoot!
Kiểm dây nỏ trước khi bắn! | Check the crossbow string before shooting!
Lắp tên, giữ đúng mục tiêu! | Load the bolt, hold on the target!
Đợi lệnh mới buông lẫy! | Await the order before releasing!
Cùng giữ thế bắn nỏ! | Hold the crossbow shooting stance together!
Nhắm nỏ cho chắc rồi bắn! | Aim the crossbow steadily, then shoot!
''')
add('gun','A1','''
Đưa súng lên! | Raise the gun!
Nhắm súng đây! | Aim the gun here!
Chờ rồi hãy bắn! | Wait before shooting!
Giữ súng thẳng! | Keep the gun straight!
Bắn vào đó thôi! | Shoot there!
Tôi đã sẵn súng! | My gun is ready!
''')
add('gun','A3','''
Cùng giữ hàng súng! | Keep the gun rank together!
Theo hiệu mới khai hỏa! | Fire only on the signal!
Giữ súng hướng mục tiêu! | Keep guns towards the target!
Chờ nhau rồi cùng bắn! | Wait for each other, then fire!
Nhắm kỹ, đừng bắn vội! | Aim carefully, do not fire too soon!
Đã sẵn súng, giữ vị trí! | Guns ready, hold position!
''')
add('gun','A4','''
Đã nhận lệnh, chuẩn bị khai hỏa! | Order received, prepare to fire!
Giữ nòng súng đúng hướng! | Keep the muzzle pointed correctly!
Cùng bắn theo hiệu lệnh! | Fire together on command!
Chờ mục tiêu vào tầm súng! | Wait for the target to enter gun range!
Kiểm súng, giữ chắc tay! | Check the gun, keep a firm grip!
Khai hỏa vào mục tiêu đã chỉ! | Fire at the indicated target!
''')
add('elephant_move','A1','''
Dẫn voi đi thôi. | Lead the elephant on.
Voi đi lối này. | Elephant, this way.
Chậm lại, giữ đều. | Slowly, stay steady.
Đưa voi tới đó. | Bring the elephant there.
Theo đất chắc mà qua. | Cross on firm ground.
Tôi giữ voi tiến. | I will keep the elephant moving.
''')
add('elephant_move','A3','''
Cùng đưa voi tiến lên. | Bring the elephants forward together.
Giữ đều bước voi. | Keep the elephant's pace steady.
Theo hàng qua lối rộng. | Follow the line along the wide way.
Chờ voi sau rồi tiến. | Wait for the elephant behind, then advance.
Tôi dẫn voi theo hiệu. | I will lead the elephant on the signal.
Giữ chỗ cho voi qua. | Leave room for the elephant to pass.
''')
add('elephant_move','A4','''
Theo lệnh, đưa voi tới nơi. | Bring the elephant into position on orders.
Giữ hướng tiến voi đã định. | Keep the elephant on its chosen heading.
Chọn đất vững cho voi đi. | Choose firm ground for the elephant.
Tôi nhận việc dẫn voi này. | I will lead this elephant.
Cùng tiến, giữ khoảng cách voi. | Advance together, keep the elephants spaced.
Đưa voi qua lối đã chỉ. | Bring the elephant along the indicated route.
''')
add('siege_attack','A1','''
Nhắm máy vào đó! | Aim the engine there!
Đánh tới thôi! | Strike forward!
Giữ máy cho vững! | Keep the engine steady!
Chờ rồi cùng đánh! | Wait, then strike together!
Tôi đã sẵn tay! | I am ready!
Đánh vào chỗ ấy! | Strike that spot!
''')
add('siege_attack','A3','''
Cùng giữ hướng máy! | Hold the engine's aim together!
Chờ hiệu rồi đánh tới! | Await the signal, then strike!
Nhắm theo chỗ đã chỉ! | Aim at the indicated spot!
Giữ vững máy khi đánh! | Steady the engine while attacking!
Đội máy, cùng chuẩn bị! | Engine crew, prepare together!
Đánh đúng mục tiêu này! | Strike this target correctly!
''')
add('siege_attack','A4','''
Đội máy, chờ lệnh đánh! | Engine crew, await the attack order!
Kiểm hướng trước khi khai hỏa! | Check the aim before firing!
Cùng đánh vào mục tiêu đã định! | Strike the chosen target together!
Máy đã chuẩn bị, giữ vị trí! | Engine prepared, hold position!
Theo hiệu lệnh mà đánh tới! | Strike forward on command!
Giữ máy vững, đánh tiếp! | Steady the engine, strike again!
''')
add('sail','A1','''
Thuyền đi thôi. | Boat, move on.
Theo nước mà đi. | Follow the waterway.
Giữ lái đây. | Hold the helm here.
Tôi đưa thuyền tới. | I will bring the boat.
Qua luồng nước ấy. | Through that channel.
Lối thuyền ở đây. | The boat's way is here.
''')
add('sail','A3','''
Cùng đưa thuyền tiến. | Bring the vessels forward together.
Giữ luồng đi cho đều. | Keep steadily to the channel.
Theo thuyền trước mà tới. | Follow the vessel ahead.
Chọn nước sâu rồi qua. | Choose deep water, then cross.
Giữ lái theo hiệu. | Steer on the signal.
Tôi đưa thuyền theo lối ấy. | I will take the boat that way.
''')
add('sail','A4','''
Theo lệnh, đưa thuyền tới nơi. | Bring the vessel into position on orders.
Giữ đúng luồng đã chọn. | Keep to the chosen channel.
Tôi sẽ lo hướng lái này. | I will handle this heading.
Đưa thuyền theo đường nước ấy. | Take the vessel along that waterway.
Giữ lái vững khi qua luồng. | Hold the helm steady through the channel.
Đã rõ bến đến, lên đường. | Destination understood, set off.
''')
add('fish','A1','''
Thả lưới đây. | Cast the net here.
Kéo cá lên thôi. | Haul the fish up.
Tôi tìm chỗ có cá. | I will find the fish.
Gom cá vào đây. | Gather the fish here.
Lưới đã sẵn tay. | The net is ready in hand.
Theo đàn cá ấy. | Follow that shoal.
''')
add('fish','A3','''
Cùng thả lưới chỗ này. | Cast the net here together.
Giữ thuyền bên đàn cá. | Keep the boat by the shoal.
Kéo đều tay cho chắc. | Haul steadily and firmly.
Gom mẻ cá vừa được. | Gather the catch just taken.
Tôi nhận phần đánh cá. | I will take the fishing work.
Giữ lưới đúng luồng cá. | Keep the net in the shoal's path.
''')
add('fish','A4','''
Tôi sẽ lo mẻ lưới này. | I will handle this cast.
Đưa thuyền tới nơi đánh cá. | Bring the boat to the fishing ground.
Giữ đều tay khi kéo lưới. | Keep a steady pull on the net.
Gom cá cho gọn trên thuyền. | Gather the fish neatly aboard.
Lưới đã chuẩn bị, thả thôi. | The net is prepared, cast it.
Theo luồng cá, giữ hướng lái. | Follow the shoal, hold the helm.
''')
add('naval_trade','A1','''
Chở hàng đi thôi. | Carry the cargo out.
Tôi tìm bến hàng. | I will find the trading landing.
Hàng ở trên thuyền. | The cargo is aboard.
Theo sông tới đó. | Along the river there.
Đưa thuyền tới chợ. | Take the boat to market.
Giữ hàng trong thuyền. | Keep the cargo aboard.
''')
add('naval_trade','A3','''
Cùng đưa hàng tới bến chợ. | Bring the cargo to the market landing together.
Tôi nhận chuyến thuyền hàng. | I will take the cargo voyage.
Giữ hàng chắc khi đi sông. | Secure the cargo on the river.
Theo luồng tới nơi trao hàng. | Follow the channel to the trading place.
Thuyền đã đủ hàng, đi thôi. | The vessel is loaded, let us go.
Đổi hàng xong rồi quay bến. | Trade, then return to the landing.
''')
add('naval_trade','A4','''
Chuyến hàng đường sông đã sẵn. | The river shipment is ready.
Tôi sẽ đưa hàng tới đúng bến. | I will bring the cargo to the right landing.
Giữ hàng nguyên vẹn suốt chuyến. | Keep the cargo intact throughout the voyage.
Theo đường nước đã định mà buôn. | Trade along the chosen waterway.
Đã nhận bến đến, chuyển hàng. | Destination received, carry the cargo.
Tôi nhận việc chở hàng tới chợ. | I will take the cargo to market.
''')
