# Smartlead Help Documentation

*Scraped on: 2026-02-11*

*Source: https://help.smartlead.ai/*


---


## API Documentation

**URL:** https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f


[Skip to content](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f#main)

![🤖 Page icon](<Base64-Image-Removed>)![🤖 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f916.svg)

# API Documentation

## Introduction

Welcome to Smartlead’s Developer documentation. You’re here because you want to automate the day lights out of your outbound.

Smartlead’s API is very powerful and gives you flexibility to do almost everything you can do using the interface. You’ll find all that power on this page.

So lets goooo!

## Getting Started & Authentication

#### Step 1

Head to your [settings section](https://app.smartlead.ai/app/settings/profile). Click on the “Activate API button”

#### Step 2

If your plan has API access, your API key will be provided to you here. Do not share this with anyone. This is the key that acts as an identity to your account, think of it as your username & password combined.

#### Step 3

All our API’s point to our dedicated domain

https://server.smartlead.ai/api/v1

Using the API key in [step 2](https://help.smartlead.ai/a0d223bdd3154a77b3735497aad9419f#40a6a0e8603845fc936f8b5aa6e5b0a2) you can make requests to our system.

You will need to attach the API key as a query string to all the requests listed below under the query parameter

?api\_key=yourApiKey

#### Rate limits

Your API key is rate limited to 10 requests every 2 seconds

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns?api\_key=API\_KEY

​

## References

#### Campaign

A campaign refers to an outreach sequence you want to run to a list of leads with certain conditions.

#### Lead

A lead in the API is the same as the lead in your app. They are the recipient of your email / the person you’re trying to contact. Aka the people you provide value to with the awesome products/services you have to sell to them

#### Update

Whenever you need to update a campaign or a lead

#### Unsubscribe

When someone no longer wants to hear from you, they unsubscribe, aka the no more touchy zone.

#### Lead Status

STARTED: The lead is scheduled to start and is yet to receive the 1st email in the sequence.
COMPLETED: The lead has received all the emails in the campaign.
BLOCKED: A lead is blocked when the email sent is bounced or if added in the global block list
INPROGRESS: The lead has last received atleast one email in the sequence.

​

## Campaigns

### Get Campaign By Id

This endpoint fetches a campaign based on its id.

[Introduction](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#bea1ec0dcdaa4e4e941c2b401824fc9e)

[Getting Started & Authentication](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#bf41cf4760d94179acee6a2aa1de1ceb)

[Step 1](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#9d369859188d4ab99db14259b2aabbdb)

[Step 2](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#40a6a0e8603845fc936f8b5aa6e5b0a2)

[Step 3](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#c60473da85ba4fb798dc0910ec68c31b)

[Rate limits](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#2ad64f16b375438fba2c0f6d76df3365)

[References](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#7fdadae2798b466393600cbac5526fee)

[Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#f93cc8a91cbe402590009f19bb6f9a4d)

[Lead](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#3201c72b7c0c49c8b8353e7e9becea97)

[Update](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#4ab300ca7b6248de83f9fe2dbf1d387c)

[Unsubscribe](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#df7bfd2ad55c4cfa909e4cb757f0b421)

[Lead Status](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#93383e6d79d048bdba7c2f1efcc1ec7e)

[Campaigns](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#e9dba89b188340a5bb46a4fe297ce619)

[Get Campaign By Id](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#af681d0e738f4ae8a876eb0d911492af)

[URL Parameters](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#e3f654f0f7834a28b8c4b1f355cdc51a)

[Create Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#3e4498653c974bdbaa0fb9c554c8bfce)

[Update Campaign Schedule](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#2431fe8b6c23429ab7dff82607145c45)

[Update Campaign General Settings](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#043d5473423f4b9080cb9338aa888807)

[Fetch Campaign Sequence By Campaign ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#78f164d9a799401d89f5125ed2a7efd8)

[Save Campaign Sequence](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#bad57c314d784198a897484e9cd1b3a9)

[List all Campaigns](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#883fef33eccc4542ab296f24fd61d418)

[Delete Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#2065889d79374afab342a9464748ff0e)

[List all email accounts per campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#23c5278793b64081bd452f3d433da854)

[Add Email Account To A Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#470f6087ea4e4668863d3e4a5852eb45)

[Remove Email Account From A Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#c90bed9438a8439f8cdfdb7a62e3d2af)

[Fetch all Campaigns using Lead ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#b6aae154535b49cb828ec38d350a5c6a)

[Fetch all email accounts associated to a user](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#ae1d20e56d4f49e18402b908fa69b949)

[Create an Email Account](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#5a3ec7a57f284a87a357cdc78a553b6c)

[Update Email Account](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#cb9ab6cbacfe4d8f8bf5b8050c401857)

[Fetch Email Account By ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#a6ac73a0fb3443c8829ec70fe3bd342f)

[Add/Update Warmup To Email Account](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#ec1028be75834b5a94699100bc4107cf)

[Fetch Warmup Stats By Email Account ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#94f671e5cfec4b13adb8cd54a5e6bec7)

[List all leads by campaign id](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#713a26c6080f45388521fc63e2909a86)

[Fetch lead categories](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#26b2f8c4f77c4b6f97aaef741b6e97a0)

[Fetch lead by email address](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#e8bed2e848f34b4cabe59e65cf2ff866)

[Export data from a campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#301c9e4c92774ceb8690d2eae777c980)

[Fetch Lead Message History Based On Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#9ec64e30099440749119ff169247ec9f)

[Reply To Lead From Master Inbox via API](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#23f380d414b847bcaa25ab6f7b752196)

[Fetch Campaign Statistics By Campaign Id](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#1136bf3fe8794bc28f632c4d21466dba)

[Fetch Campaign Statistics By Campaign Id And Date Range](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#6d3a4ddd82fd43ef81c50903846be73f)

[Fetch campaign top level analytics](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#bc1bc5b5dab147b3aaa04d1f1466653f)

[Add leads to a campaign by ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#c13d87234d484957aeaaefc915c2cfbe)

[Resume Lead By Campaign ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#e09d5a9aba67479e97b3f992ca0c27ed)

[Pause Lead By Campaign ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#1e335ffdbcb44806b4c908e4bf674f06)

[Delete Lead By Campaign ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#21eeba30d5324e769e99e41a2f9c5bd7)

[Unsubscribe/Pause Lead From Campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#ed26feddfff74de1b9884cc341aaf4c7)

[Unsubscribe Lead From All Campaigns](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#4245ad8d03f3432585718fc892f7132d)

[Add Lead/Domain to Globlal Block List](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#f7945fd153914a468154af193634ec0f)

[Update lead using the Lead ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#044121c9a2704b21b54a1d37d2c8a2eb)

[Update a lead’s category based on their campaign](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#2e8437777ce84763a213899a7733927f)

[Patch campaign status](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#f25b14bad3014cce9168cfe9e34a255f)

[Fetch Webhooks By Campaign ID](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#19c25df372eb45fda8eb8d6563a511a1)

[Add / Update Campaign Webhook](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#3cd0ed7db3784ce6b8c4812eed5ebeb6)

[Delete Campaign Webhook](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#04d365bdeaea47439622ae68baed1f99)

[Add Client To System (Whitelabel or not)](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#934641f56eaf4931b0bd28f5eeda5da0)

[Fetch all clients](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#f2c4fc5bb6f34e1098afef18c4468d16)

[Reconnect failed email accounts](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25#1b64841db9f04f90b89521a22599bdee)

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}?api\_key={API\_KEY}

​

The above request yields the below JSON response

> Response - JSON of campaign

{"id":372"user\_id":124"created\_at":"2022-05-26T03:47:31.448094+00:00""updated\_at":"2022-05-26T03:47:31.448094+00:00""status":"ACTIVE"// ENUM (DRAFTED/ACTIVE/COMPLETED/STOPPED/PAUSED)"name":"My Epic Campaign""track\_settings":"DONT\_REPLY\_TO\_AN\_EMAIL"// ENUM (DONT\_EMAIL\_OPEN/DONT\_LINK\_CLICK/DONT\_REPLY\_TO\_AN\_EMAIL)"scheduler\_cron\_value":"{ tz: 'Australia/Sydney', days: \[ 1, 2, 3, 4, 5 \], endHour: '23:00', startHour: '10:00' }""min\_time\_btwn\_emails":10// minutes"max\_leads\_per\_day":10"stop\_lead\_settings":"REPLY\_TO\_AN\_EMAIL"// ENUM (REPLY\_TO\_AN\_EMAIL/CLICK\_ON\_A\_LINK/OPEN\_AN\_EMAIL)"unsubscribe\_text":"Don't Contact Me","client\_id":23// null if the campaign is not attached to a client,"enable\_ai\_esp\_matching":true,// leads will be matched with similar ESP mailboxes IF they exist, else normal sending occurs"send\_as\_plain\_text":true,// emails for this campaign are sent as plain text (parsing out any html)"follow\_up\_percentage":40% // the follow up percetange allocated - it is assumed 60% is new leads}

​

#### URL Parameters

| Parameter | Description |
| --- | --- |
| campaign\_id | The ID of the campaign you want to fetch |

### Create Campaign

This endpoint creates a campaign

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/create?api\_key=${API\_KEY}--data {"name":"Test email campaign","client\_id":22// leave null if no client }

​

The above request yields the below JSON response

> Response - JSON of campaign

{
ok:true,
id:3023,
name:"Test email campaign",
created\_at:2022-11-07T16:23:24.025929+00:00}

​

### Update Campaign Schedule

This endpoint updates a campaign’s schedule.

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/schedule?api\_key=${API\_KEY}
--data {"timezone":"America/Los\_Angeles","days\_of\_the\_week":\[1\],// \[0,1,2,3,4,5,6\]"start\_hour":"01:11",// "09:00""end\_hour":"02:22",// "18:00""min\_time\_btw\_emails":10,// time in minutes between emails"max\_new\_leads\_per\_day":20// max new leads per day"schedule\_start\_time":"2023-04-25T07:29:25.978Z"// Standard ISO format accepted}

​

Please use the Timezones available here:

[Timezones](https://help.smartlead.ai/Timezones-20fcff9ddbb5441790c7c8e5ce0e9233?pvs=25)

The above request yields the below JSON response

> Response - JSON of campaign

{
ok:true,}

​

Error400 -

BED REQUEST

{"error":"Invalid timezone - {timezone}"}

{"error":"Invalid start\_hour - {startHour}"}

{"error":"Invalid end\_hour - {endHour}"}

{"error":"startHour cannot be greater that endHour"}

​

### Update Campaign General Settings

This endpoint updates a campaign’s general settings

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/settings?api\_key=${API\_KEY}
--data {"track\_settings":\["DONT\_TRACK\_EMAIL\_OPEN"\],// allowed values are -> DONT\_TRACK\_EMAIL\_OPEN \| DONT\_TRACK\_LINK\_CLICK \| DONT\_TRACK\_REPLY\_TO\_AN\_EMAIL"stop\_lead\_settings":"REPLY\_TO\_AN\_EMAIL",// allowed values are -> CLICK\_ON\_A\_LINK \| OPEN\_AN\_EMAIL"unsubscribe\_text":"","send\_as\_plain\_text":false,"follow\_up\_percentage":100,// max allowed 100 min allowed 0"client\_id":33// leave as null if not needed,"enable\_ai\_esp\_matching":true// by default is false}

​

The above request yields the below JSON response

> Response - JSON of campaign

{
ok:true,}

​

Error400 -

BED REQUEST

Invalid track\_settings value - {trackSettings}

{"error":"Invalid stop\_lead\_settings value - {stopLeadSettings}"}

​

### Fetch Campaign Sequence By Campaign ID

This endpoint fetches a campaign’s sequence data

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/sequences?api\_key=${API\_KEY}

​

The above request yields the below JSON response

> Response - JSON of <campaign\_sequence>

{"id":8494,"created\_at":"2022-11-08T07:06:35.990Z","updated\_at":"2022-11-08T07:34:03.667Z","email\_campaign\_id":3070,"seq\_number":1,"subject":"","email\_body":"","sequence\_variants":\[{"id":2535,"created\_at":"2022-11-08T07:06:36.002558+00:00","updated\_at":"2022-11-08T07:34:04.026626+00:00","is\_deleted":false,"subject":"Subject","email\_body":"<p>Hi<br><br>How are you?<br><br>Hope you're doing good</p>","email\_campaign\_seq\_id":8494,"variant\_label":"A"},{"id":2536,"created\_at":"2022-11-08T07:06:36.002558+00:00","updated\_at":"2022-11-08T07:34:04.373866+00:00","is\_deleted":false,"subject":"Ema a","email\_body":"<p>This is a new game a</p>","email\_campaign\_seq\_id":8494,"variant\_label":"B"},{"id":2537,"created\_at":"2022-11-08T07:06:36.002558+00:00","updated\_at":"2022-11-08T07:34:04.721608+00:00","is\_deleted":false,"subject":"C emsil","email\_body":"<p>Hiii C</p>","email\_campaign\_seq\_id":8494,"variant\_label":"C"}\]}

​

### Save Campaign Sequence

This endpoint saves a sequence within a campaign

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/sequences?api\_key=${API\_KEY}
--data {"sequences":\[{"id":8494,"seq\_number":1,"seq\_delay\_details":{"delay\_in\_days":1},"seq\_variants":\[{"subject":"Subject","email\_body":"<p>Hi<br><br>How are you?<br><br>Hope you're doing good</p>","variant\_label":"A","id":2535// don't pass the ID key value pair when creating only pass for updating},{"subject":"Ema a","email\_body":"<p>This is a new game a</p>","variant\_label":"B","id":2536// don't pass the ID key value pair when creating only pass for updating},{"subject":"C emsil","email\_body":"<p>Hiii C</p>","variant\_label":"C","id":2537// don't pass the ID key value pair when creating only pass for updating}\]},{"id":8495,"seq\_number":2,"seq\_delay\_details":{"delay\_in\_days":1},"subject":"",// blank makes the follow up in the same thread"email\_body":"<p>Bump up right!</p>"}\]}

​

The above request yields the below JSON response

> Response - JSON of success message

{"ok":true,"data":"success"}

​

Error404 -

NOT FOUND

{"error":"Campaign not found - Invalid campaign\_id."}

​

### List all Campaigns

This endpoint fetches all the campaigns in your account

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns?api\_key={API\_KEY}

​

The above request yields an array of JSONs like below

> Response - List of <email\_campaign> schema

\[\
...,{"id":372,"user\_id":124,"created\_at":"2022-05-26T03:47:31.448094+00:00","updated\_at":"2022-05-26T03:47:31.448094+00:00","status":"ACTIVE",// ENUM (DRAFTED/ACTIVE/COMPLETED/STOPPED/PAUSED)"name":"My Epic Campaign","track\_settings":"DONT\_REPLY\_TO\_AN\_EMAIL",// ENUM (DONT\_EMAIL\_OPEN/DONT\_LINK\_CLICK/DONT\_REPLY\_TO\_AN\_EMAIL)"scheduler\_cron\_value":"{ tz: 'Australia/Sydney', days: \[ 1, 2, 3, 4, 5 \], endHour: '23:00', startHour: '10:00' }","min\_time\_btwn\_emails":10,// minutes"max\_leads\_per\_day":10,"stop\_lead\_settings":"REPLY\_TO\_AN\_EMAIL",// ENUM (REPLY\_TO\_AN\_EMAIL/CLICK\_ON\_A\_LINK/OPEN\_AN\_EMAIL)"unsubscribe\_text":"Don't Contact Me","client\_id":22// null if not attached to a client},...\]

​

### Delete Campaign

This endpoint deletes the campaigns in your account

> API Reference ![🛫](<Base64-Image-Removed>) DELETE

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}?api\_key={API\_KEY}

​

The above request yields an array of JSONs like below

> Response - Success Response

{"ok":true}

​

### List all email accounts per campaign

This endpoint fetches all the email accounts used for sending emails to leads in the campaign

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/email-accounts?api\_key={API\_KEY}

​

The above request yields an array of JSONs like below

> Response - List of <email\_account> schema

\[\
...,{"id":24"created\_at":"2022-05-26T03:47:31.448094+00:00""updated\_at":"2022-05-26T03:47:31.448094+00:00""user\_id":123"from\_name":"Cristiano Rolando""from\_email":"cristiano@mufc.com""username":"cristiano@mufc.com""smtp\_host":"smtp.gmail.com""smtp\_port":993"smtp\_port\_type":"SSL""message\_per\_day":100"different\_reply\_to\_address":"""is\_different\_imap\_account":false"imap\_username":"cristiano@mufc.com""imap\_host":"imap.gmail.com""imap\_port":495"imap\_port\_type":"SSL""signature":"""custom\_tracking\_domain":"http://emailtracking.goldenboot.com""bcc\_email":"""is\_smtp\_success":true"is\_imap\_success":true"smtp\_failure\_error":"""imap\_failure\_error":"""type":"GMAIL"// ENUM (SMTP / GMAIL / ZOHO / OUTLOOK)"daily\_sent\_count":48},...\]

​

### Add Email Account To A Campaign

This endpoint lets you add an email account to a campaign

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/email-accounts?api\_key=${API\_KEY}
\-\- data {"email\_account\_ids":\[2907\]}

​

The above request yields success/failure response

> Response - List of <results> schema

{"ok":true,"result":\[{"id":46417,"email\_campaign\_id":1353,"email\_account\_id":2907,"updated\_at":"2022-11-07T15:28:18.171Z"}\],}

​

Error400 -

BED REQUEST

{"error":"Email account id - 297 not allowed. Permission Error."}

​

Error404 -

NOT FOUND

{"error":"Campaign not found - Invalid campaign\_id."}

​

### Remove Email Account From A Campaign

This endpoint lets you delete an email account from a campaign

> API Reference ![🛫](<Base64-Image-Removed>) DELETE

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/email-accounts?api\_key=${API\_KEY}
\-\- data {"email\_account\_ids":\[2907\]}

​

The above request yields success/failure response

> Response - List of <results> schema

{"ok":true,"result":1}

​

Error400 -

BED REQUEST

{"error":"Email account id - 297 not allowed. Permission Error."}

​

Error404 -

NOT FOUND

{"error":"Campaign not found - Invalid campaign\_id."}

​

### Fetch all Campaigns using Lead ID

This endpoint lets you fetch all the campaigns a Lead belongs to using the Lead ID

> API Reference ![🛫](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/leads/<lead\_id>/campaigns?api\_key=${API\_KEY}

​

The above request yields the results schema below

> Response - List of <results> schema

\[{"id":2911,"status":"COMPLETED","name":"SL - High Intent Leads guide"},{"id":5055,"status":"DRAFTED","name":""}\]

​

### Fetch all email accounts associated to a user

This endpoint fetches all the email accounts used for sending emails to leads in the campaign

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/email-accounts/?api\_key=<API\_KEY>&offset=0&limit=10

// default value
// offset = 0, limit = 100

// min value
// offset = 0

// max value
// limit = 100

​

The above request yields an array of JSONs like below

> Response - List of <email\_account> schema

\[\
...,{"id":24"created\_at":"2022-05-26T03:47:31.448094+00:00""updated\_at":"2022-05-26T03:47:31.448094+00:00""user\_id":123"from\_name":"Cristiano Rolando""from\_email":"cristiano@mufc.com""username":"cristiano@mufc.com""password":"potato""imap\_password":"gogopotato""smtp\_host":"smtp.gmail.com""smtp\_port":993"smtp\_port\_type":"SSL""message\_per\_day":100"different\_reply\_to\_address":"""is\_different\_imap\_account":false"imap\_username":"cristiano@mufc.com""imap\_host":"imap.gmail.com""imap\_port":495"imap\_port\_type":"SSL""signature":"""custom\_tracking\_domain":"http://emailtracking.goldenboot.com""bcc\_email":"""is\_smtp\_success":true"is\_imap\_success":true"smtp\_failure\_error":"""imap\_failure\_error":"""type":"GMAIL"// ENUM (SMTP / GMAIL / ZOHO / OUTLOOK)"daily\_sent\_count":48,"client\_id":33// null if it is not attached to a client"warmup\_details":{"id":99200,"status":"INACTIVE","total\_sent\_count":7,"total\_spam\_count":0,"warmup\_reputation":"100%"}},...\]

​

### Create an Email Account

This endpoint updates a specific email account based on the id provided in the JSON body

> API Reference ![🛬](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/email-accounts/save?api\_key=${API\_KEY}--data {"id":2849,// set null to create new email account"from\_name":"Ramesh","from\_email":"ramesh@five2one.com.au","user\_name":"ramesh@five2one.com.au","password":"gjfsvtyrqpemuqzf","smtp\_host":"smtp.gmail.com","smtp\_port":465,"imap\_host":"imap.gmail.com","imap\_port":993,"max\_email\_per\_day":100,"custom\_tracking\_url":"","bcc":"","signature":"","warmup\_enabled":false,// set true to enable warmup"total\_warmup\_per\_day":null,"daily\_rampup":null,// set value to enable ramup"reply\_rate\_percentage":null,"client\_id":null,// set value to assign to client id}

​

The above request yields a JSON like below

> Response Success 200 OK

{"ok":true,"message":"Email account added/updated successfully!","emailAccountId":2849,"warmupKey":"apple-keyes"}

​

> Response Failure Bad Request 400

Error 400 BAD\_REQUEST - ACCOUNT\_ALREADY\_EXIST

{
ok:false,
message: 'Email account already added by other user.',
errorCode: 'ACCOUNT\_ALREADY\_EXIST',
emailAccountId:null}

​

{
ok:false,
message: 'Email account already exist. Please pass id to update it',
errorCode: 'ACCOUNT\_ALREADY\_EXIST',
emailAccountId: ${existingAccountId}}

​

Error 404 NOT\_FOUND - ACCOUNT\_NOT\_FOUND

{
ok: false,
message: 'Email account not found!',
errorCode: 'ACCOUNT\_NOT\_FOUND',
emailAccountId: emailAccountData.id
}

​

Error - ACCOUNT\_VERIFICATION\_FAILED

{
ok: false,
message: 'Email account verification failed. Please verify account details.',
errorCode: 'ACCOUNT\_VERIFICATION\_FAILED',
emailAccountId: emailAccountData.id,
error: e.message
}

​

### Update Email Account

This endpoint updates an email account

> API Reference ![🛬](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/email-accounts/<email\_account\_id>?api\_key=<api\_key>
--data {"max\_email\_per\_day":100,"custom\_tracking\_url":"","bcc":"ramesh@five2one.com.au","signature":"Thanks,</br>Ramesh Kumar M","client\_id":22// leave as null if this is not needed"time\_to\_wait\_in\_mins":3// minimum integer time (in minutes) to wait before sending next email using this email account (leave null if not needed)}

​

The above request yields a success response

> Response

{"ok":true,"message":"Email account details updated successfully!","emailAccountId":10607}

​

### Fetch Email Account By ID

This endpoint gets all email details by Account ID

> API Reference ![🛫](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/email-accounts/<account\_id>/?api\_key=<API\_KEY>

​

The above request yields success/failure response

> Response

{"id":106466,"created\_at":"2023-04-18T09:02:46.060Z","updated\_at":"2023-05-30T06:06:20.587Z","user\_id":2,"from\_name":"Vaibhav","from\_email":"vaibhav@five2one.engineering","username":"vaibhav@five2one.engineering","password":"xuF\_aj4u","smtp\_host":"smtp.zoho.com.au","smtp\_port":465,"smtp\_port\_type":"SSL","message\_per\_day":200,"different\_reply\_to\_address":"","is\_different\_imap\_account":false,"imap\_username":"","imap\_password":"","imap\_host":"imap.zoho.com.au","imap\_port":993,"imap\_port\_type":"SSL","signature":null,"custom\_tracking\_domain":"","bcc\_email":null,"is\_smtp\_success":true,"is\_imap\_success":true,"smtp\_failure\_error":null,"imap\_failure\_error":null,"type":"SMTP","daily\_sent\_count":0,"client\_id":null,"warmup\_details":{"id":99200,"status":"INACTIVE","created\_at":"2023-04-18T09:02:54.822507+00:00","reply\_rate":20,"warmup\_key\_id":"brass-sleep","blocked\_reason":null,"total\_sent\_count":7,"total\_spam\_count":0,"warmup\_max\_count":40,"warmup\_min\_count":3,"is\_warmup\_blocked":false,"max\_email\_per\_day":40,"warmup\_reputation":"100%"}}

​

### Add/Update Warmup To Email Account

This endpoint lets you add / update the warmup settings to an email account

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/email-accounts/<email\_account\_id>/warmup?api\_key=<api\_key>
--data{"warmup\_enabled":true,// set false to disable warmup"total\_warmup\_per\_day":35,"daily\_rampup":2,// set this value to have daily ramup increase in warmup emails"reply\_rate\_percentage":38,"warmup\_key\_id":"apple-juice"//string value if passed will update the custom warmup-key identifier}

​

The above request yields success/failure response

> Response

{"ok":true,"message":"Email warmup details updated successfully!","emailAccountId":10607,"warmupKey":"banan-apple"}

​

### Fetch Warmup Stats By Email Account ID

This endpoint fetches stats for the last 7 days by the email account id

> API Reference ![🛫](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/email-accounts/<email\_account\_id>/warmup-stats?api\_key=<api\_key>

​

The above request yields success/failure response

> Response

{"id":106466,"sent\_count":"0","spam\_count":"0","inbox\_count":"0","warmup\_email\_received\_count":"0","stats\_by\_date":\[{"id":1,"date":"2023-05-23","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":2,"date":"2023-05-24","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":3,"date":"2023-05-25","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":4,"date":"2023-05-26","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":5,"date":"2023-05-27","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":6,"date":"2023-05-28","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":7,"date":"2023-05-29","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0},{"id":8,"date":"2023-05-30","sent\_count":0,"reply\_count":0,"save\_from\_spam\_count":0}\]}

​

### List all leads by campaign id

This endpoint fetches all the leads in a campaign using the campaign’s ID

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads?api\_key={API\_KEY}&offset={number}&limit={number}

​

The above request yields an array of JSONs like below

> Response - List of <lead\_result\_data> schema

{"total\_leads":823,"offset":10,"limit":100"data":\[{"campaign\_lead\_map\_id":23"status":"SENT""created\_at":"2022-05-26T03:47:31.448094+00:00""lead":{"id":423"first\_name":"Cristiano""last\_name":"Ronaldo""email":"cristiano@mufc.com""phone\_number":0239392029"company\_name":"Manchester United""website":"mufc.com""location":"London""custom\_fields":{"Title":"Regional Manager","First\_Line":"Loved your recent post about remote work on Linkedin"}"linkedin\_profile":"http://www.linkedin.com/in/cristianoronaldo""company\_url":"mufc.com""is\_unsubscribed":false}}\]}

​

### Fetch lead categories

This endpoint fetches all your categories

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/leads/fetch-categories?api\_key=${API\_KEY}

​

The above request yields an array of JSONs like below

> Response - List of <category\_result\_data> schema

\[{"id":1,"created\_at":"2022-08-30T12:32:48.645Z","name":"Interested"},{"id":2,"created\_at":"2022-08-30T12:32:55.159Z","name":"Meeting Request"},{"id":3,"created\_at":"2022-08-30T12:33:02.286Z","name":"Not Interested"},{"id":4,"created\_at":"2022-08-30T12:33:09.895Z","name":"Do Not Contact"},{"id":5,"created\_at":"2022-08-30T12:33:16.204Z","name":"Information Request"},{"id":6,"created\_at":"2022-08-30T12:33:22.323Z","name":"Out Of Office"},{"id":7,"created\_at":"2022-08-30T12:33:28.519Z","name":"Wrong Person"}\]

​

### Fetch lead by email address

This endpoint fetches a lead’s data using the email address

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/leads/?api\_key=${API\_KEY}&email=${email}

​

The above request yields a JSON

> Response - <lead> schema

{"id":"627657","first\_name":"Ramesh","last\_name":"Madanlal","email":"m.rameshkumarjain@gmail.com","created\_at":"2022-08-29T06:15:31.513Z","phone\_number":"9042859097","company\_name":"Five2One","website":"www.five2one.com.au","location":"India","custom\_fields":{},"linkedin\_profile":"","company\_url":"","is\_unsubscribed":false}

​

### Export data from a campaign

This endpoint returns a CSV file of all leads from a campaign using the campaign’s ID

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads-export?api\_key={API\_KEY}

​

The above request yields the csv format below

> Response <csv with columns>

id - integer
campaign\_lead\_map\_id - integer
status - text
created\_at - timestamp with time zone
first\_name - text
last\_name - text
email - text
phone\_number - text
company\_name - text
website - text
location - text
custom\_fields - jsonb
linkedin\_profile - text
company\_url - text
is\_unsubscribed - boolean
last\_email\_sequence\_sent - integer
is\_interested - boolean
open\_count - integer
click\_count - integer
reply\_count- integer

​

### Fetch Lead Message History Based On Campaign

This endpoint returns an array containing the entire message history of a lead specific to a campaign (Same data as in the master inbox)

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads/{lead\_id}/message-history?api\_key={API\_KEY}

​

The above request yields the csv format below

> Response JSON Array

"history":\[{"type":"SENT","message\_id": <sw-uibo3i2hoi-ced32-23iuboufde-23oub@outlook.com>\
"stats\_id": "iuh2o3iuh3o2ih2-iuho3-edwhi92-oiho3-3223oihoi9uf\
"time":"2023-03-13T07:44:12.978Z","email\_body":"<div>Hi Christiano, lets do the SIIUUUU</div>","subject":"Quick question for you, Ronaldo"},{"type":"SENT","message\_id": <sw-uibo3i2hoi-ced32-23iuboufde-23oub@outlook.com>\
"stats\_id": "iuh2o3iuh3o2ih2-iuho3-edwhi92-oiho3-3223oihoi9uf\
"time":"2023-03-15T07:50:56.673Z","email\_body":"<div>Hi Christiano, it's okay if Messi was offerred more money</div>","subject":"RE: Quick question for you, Ronaldo"},{"type":"REPLY","message\_id": <sw-uibo3i2hoi-ced32-23iuboufde-23oub@outlook.com>\
"stats\_id": "iuh2o3iuh3o2ih2-iuho3-edwhi92-oiho3-3223oihoi9uf\
"time":"2023-03-15T09:13:29.000Z","email\_body":"<p>Yes, I was upset but I am fine, I have bugatti</p>"}\],"from":"j\_s@smartlead-outbound.com","to":"ronaldo.christiano@siu.io"

​

### Reply To Lead From Master Inbox via API

This endpoint allows you to reply to a lead using the Master Inbox API

> API Reference ![🛬](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/${campaign\_id}/reply-email-thread?api\_key={API\_KEY}--body

{// email\_stats\_id unique id per lead per email sequence per campaign (Can be fetched via email campaigns -> lead ->message-history API)"email\_stats\_id":"a739fed0-c965-47e3-8f36-3e6d2805acec",//reply message email body "email\_body":"Hey just testing reply from master inbox!",// message\_id to which email will sent reply (Can be fetched via email campaigns -> lead -> message-history API) "reply\_message\_id":"<CAAfSCXmLWEUF1rc4Hc4D5d1m4+jORS+Sg-pCV2ErfGju+mUOOw@mail.gmail.com>",// the time of the message to which the reply message is sent (Can be fetched via email campaigns -> lead -> message-history API)"reply\_email\_time":"2023-06-19T08:10:35.000Z",// the message to which the reply message is sent (Can be fetched via email campaigns -> lead -> message-history API)"reply\_email\_body":"<html><head>\\r\\n<meta http-equiv=\\"Content-Type\\" content=\\"text/html; charset=utf-8\\"></head><body><div dir=\\"ltr\\"><div dir=\\"ltr\\">Interested</div><br><div class=\\"gmail\_quote\\"><div dir=\\"ltr\\" class=\\"gmail\_attr\\">On Mon, Jun 19, 2023 at 1:23 PM Ramesh Kumar &lt;<a href=\\"mailto:m.rameshkumarjain@outlook.com\\">m.rameshkumarjain@outlook.com</a>&gt; wrote:<br></div><blockquote class=\\"gmail\_quote\\" style=\\"margin:0px 0px 0px 0.8ex; border-left:1px solid rgb(204,204,204); padding-left:1ex\\"><u></u><div><div>I'm testing webhook. Please click below -&nbsp;</div><div><br></div><div><a href=\\"https://click.sleadtrack.com/link?messageId=%3Csw-a739fed0-c965-47e3-8f36-3e6d2805acec%40outlook.com%3E&amp;url=https%3A%2F%2Fwww.google.com%2F\\" target=\\"\_blank\\">https://www.google.com/</a></div><div><br></div><div>Thanks,</div><div>Ramesh</div><p></p><p style=\\"font-size:12px\\"><a href=\\"https://open.sleadtrack.com/unsubscribe?messageId=%3Csw-a739fed0-c965-47e3-8f36-3e6d2805acec@outlook.com%3E\\" target=\\"\_blank\\">unsubscribe here </a></p><img src=\\"https://open.sleadtrack.com/image?messageId=%3Csw-a739fed0-c965-47e3-8f36-3e6d2805acec@outlook.com%3E\\" alt=\\"\\" title=\\"\\" width=\\"1\\" height=\\"1\\" style=\\"display:none\\"> </div></blockquote></div><br clear=\\"all\\"><div><br></div><span class=\\"gmail\_signature\_prefix\\">-- </span><br><div dir=\\"ltr\\" class=\\"gmail\_signature\\"><div dir=\\"ltr\\"><div><div dir=\\"ltr\\"><div>Thanks &amp; Regards,</div><div>Dinesh Kumar M.</div></div></div></div></div></div></body></html>","cc":"m.rameshkumarjain@gmail.com","bcc":"ramesh@five2one.com.au","add\_signature":true}

​

The above request yields a response code

> Response Status Code Array

200 OK: Email added to the queue, will be sent out soon!

​

### Fetch Campaign Statistics By Campaign Id

This endpoint fetches campaign statistics using the campaign’s ID

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/statistics?api\_key={API\_KEY}&offset={number}&limit={number}// OPTIONAL QUERY PARAMS
email\_sequence\_number={number}// 1,2,3,4
email\_status={string}// possible values -> 'opened' or 'clicked' or 'replied' or 'unsubscribed' or 'bounced'

​

The above request yields an array of JSONs like below

> Response - List of <stats\_result\_data> schema

{"total\_stats":"419","data":\[{"lead\_name":"Charles Newson","lead\_email":"charles@newson.io","lead\_category":null,"sequence\_number":1,"email\_campaign\_seq\_id":1178,"seq\_variant\_id":129,"email\_subject":"Smartlead - Charles","email\_message":"<p>Hey Charles!</p>","sent\_time":"2022-08-02T12:49:11.747Z","open\_time":null,"click\_time":null,"reply\_time":null,"open\_count":0,"click\_count":0,"is\_unsubscribed":false,"is\_bounced":false}\],"offset":0,"limit":1}

​

### Fetch Campaign Statistics By Campaign Id And Date Range

This endpoint fetches campaign statistics using the campaign’s ID

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/3745/analytics-by-date?api\_key={API\_KEY}&start\_date=2022-12-16&end\_date=2022-12-23

​

The above request yields an array of JSONs like below

> Response - List of <stats\_result\_data> schema

{"id":3745,"user\_id":2,"created\_at":"2022-11-21T15:21:58.042Z","status":"ACTIVE","name":"Sai \| General","start\_date":"2022-12-16","end\_date":"2022-12-23","sent\_count":"4375","open\_count":"745","click\_count":"2","reply\_count":"11","block\_count":"0","total\_count":"84777","drafted\_count":"62392","bounce\_count":"289","unsubscribed\_count":"0"}

​

Error response: (

400 Bad Request

)

{
"error": "Invalid start\_date & end\_date range. Date difference should be max of 30days."
}

​

{
"error": "Invalid campaign id'"
}

​

### Fetch campaign top level analytics

This endpoint returns a campaigns top level analytics

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/analytics?api\_key=${API\_KEY}

​

The above request yields a JSON with the below format

> Response <campaign\_analytics> schema

{"id":979,"user\_id":288,"created\_at":"2022-08-29T06:15:31.458Z","status":"COMPLETED","name":"",// email stats"sent\_count":"14","open\_count":"14","click\_count":"0","reply\_count":"4","block\_count":"0","total\_count":"14","drafted\_count":"0","bounce\_count":"0","unsubscribed\_count":"0",// total no of sequences"sequence\_count":"2",// tags"tags":\[{"id":44,"name":"ramesh","color":"#FCB1D0"}\],// total unique lead open count"unique\_open\_count":"7",// total unique clicks"unique\_click\_count":"8",// total leads reached at this point"unique\_sent\_count":"10",// client id"client\_id":6,"client\_name":"Alex James","client\_email":"alex@carrot.com"// parent campaign id (if request campaign-id is sub-sequence)"parent\_campaign\_id":null,// campaign lead stats"campaign\_lead\_stats":{"total":8,"blocked":0,"stopped":0,"completed":8,"inprogress":0,"notStarted":0}}

​

### Add leads to a campaign by ID

This endpoint adds leads to a campaign using the campaign’s ID

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads?api\_key={API\_KEY}--data '{"lead\_list": List<lead\_input> \*(max 100 leads)}'

​

In the above

List<lead\_input>

is an array of JSON objects that look like this:

{
lead\_list:\[{"first\_name":"Cristiano""last\_name":"Ronaldo""email":"cristiano@mufc.com""phone\_number":0239392029"company\_name":"Manchester United""website":"mufc.com""location":"London""custom\_fields":{"Title":"Regional Manager","First\_Line":"Loved your recent post about remote work on Linkedin"}// max 20 fields"linkedin\_profile":"http://www.linkedin.com/in/cristianoronaldo""company\_url":"mufc.com"}\],"settings":{"ignore\_global\_block\_list":true,// true ignores leads uploaded in the lead list that are part of your global/client level block list"ignore\_unsubscribe\_list":true,// true ignores leads uploaded in the lead list that have unsubsribed previously"ignore\_duplicate\_leads\_in\_other\_campaign":false// false allows leads to be added to this campaign even if they exist in another campaign}}

​

The above request yields the below JSON

> Response - <add\_leads\_response> schema

{"ok":true"upload\_count":240"total\_leads":400"already\_added\_to\_campaign":200"duplicate\_count":150// duplicate emails"invalid\_email\_count":40// invalid formatted emails"unsubscribed\_leads":10// leads that previously unsubscribed from your outreach}

​

### Resume Lead By Campaign ID

This endpoint resumes a lead from a campaign based on the lead and campaign ID

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads/{lead\_id}/resume?api\_key={API\_KEY}--body {“resume\_lead\_with\_delay\_days”:10}// resume\_lead\_with\_delay\_days can be null and defaults to 0

​

The above request yields a success/failure JSON

> Response - <resume\_lead\_response> schema

{"ok":true,"data":"success"}

​

### Pause Lead By Campaign ID

This endpoint pauses a lead from a campaign based on the lead and campaign ID

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads/{lead\_id}/pause?api\_key={API\_KEY}

​

The above request yields a success/failure JSON

> Response - <pause\_lead\_response> schema

{"ok":true,"data":"success"}

​

### Delete Lead By Campaign ID

This endpoint deletes a lead from a campaign based on the lead and campaign ID

> API Reference ![🛫](<Base64-Image-Removed>) DELETE

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads/{lead\_id}?api\_key={API\_KEY}

​

The above request yields a success/failure JSON

> Response - <delete\_lead\_response> schema

{"ok":true}

​

### Unsubscribe/Pause Lead From Campaign

This endpoint unsubscribe a lead from a campaign based on the lead and campaign ID. Think of this as a “pause”

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/${campaign\_id}/leads/${lead\_id}/unsubscribe?api\_key={API\_KEY}

​

The above request yields a success/failure JSON

> Response - <unsubscribe\_lead\_repsonse> schema

{"ok":true}

​

### Unsubscribe Lead From All Campaigns

This endpoint unsubscribe a lead from all campaigns the lead belongs to and prevents it from being added to any future campaigns

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/leads/${lead\_id}/unsubscribe?api\_key=${API\_KEY}

​

The above request yields a success/failure JSON

> Response - <unsubscribe\_lead\_global\_repsonse> schema

200 OK {"ok":true}404 NOT FOUND {"error":"Lead not found - Invalid lead\_id."}

​

### Add Lead/Domain to Globlal Block List

This endpoint adds a lead/domain to the global block list

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/leads/add-domain-block-list?api\_key=API\_KEY--data {"domain\_block\_list":\["ramesh+1001@five2one.com.au","apple.com"\],"client\_id":null// add client\_id number if the domains/emails being added is client specific}

​

The above request yields a success/failure JSON

> Response - <unsubscribe\_lead\_repsonse> schema

{"uploadCount":1,"totalDomainAdded":1}

​

### Update lead using the Lead ID

This endpoint lets you update a lead using the lead ID

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/{campaign\_id}/leads/{lead\_id}?api\_key={API\_KEY}--data <lead\_input>

​

In the above

<lead\_input>

is a JSON object that look like this:

{"first\_name":"Cristiano""last\_name":"Ronaldo""email":"cristiano@mufc.com""phone\_number":0239392029"company\_name":"Manchester United""website":"mufc.com""location":"London""custom\_fields":{"Title":"Regional Manager","First\_Line":"Loved your recent post about remote work on Linkedin"}// max 20 fields"linkedin\_profile":"http://www.linkedin.com/in/cristianoronaldo""company\_url":"mufc.com"}

​

The above request yields a JSON like below

> Response - <update\_lead\_repsonse> schema

{"ok":true}

​

### Update a lead’s category based on their campaign

This endpoint lets you update your leads category based on the campaign they belong to

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/${campaign\_id}/leads/${lead\_id}/category?api\_key=${API\_KEY}--data {"category\_id":143,"pause\_lead":true// pause\_lead would default to false if not added}

​

The above request yields a JSON like below

> Response - <update\_category\_repsonse> schema

{"ok":true}

​

### Patch campaign status

This endpoint changes the status of a campaign

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/${<campaign\_id>}/status?api\_key={API\_KEY}
--data '{"status": "PAUSED"}' // ENUM (PAUSED / STOPPED / START)

​

The above request yields a success/failure JSON

> Response - <update\_campaign\_status\_repsonse> schema

{"ok":true}

​

### Fetch Webhooks By Campaign ID

This endpoint lets fetch all the webhooks associated to a campaign using the campaign ID

> API Reference ![🛬](<Base64-Image-Removed>) GET

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/webhooks?api\_key=${API\_KEY}

​

The above request yields success/failure response

> Response - List of <campaign\_webhook>

{"id":44,"name":"Dinesh Testing lead category webhook","created\_at":"2022-09-14T05:08:55.018Z","updated\_at":"2022-10-31T11:44:35.812Z","webhook\_url":"https://webhook.site/8222f684-0cf6-43ac-9360-28227fc36d32","email\_campaign\_id":2180,"event\_types":\["LEAD\_CATEGORY\_UPDATED"\],"categories":\["Interested"\]}

​

Possible webhook event types

WEBHOOK\_EVENT\_TYPE: {
EMAIL\_SENT: 'EMAIL\_SENT',
EMAIL\_OPEN: 'EMAIL\_OPEN',
EMAIL\_LINK\_CLICK: 'EMAIL\_LINK\_CLICK',
EMAIL\_REPLY: 'EMAIL\_REPLY',
LEAD\_UNSUBSCRIBED: 'LEAD\_UNSUBSCRIBED',
LEAD\_CATEGORY\_UPDATED: 'LEAD\_CATEGORY\_UPDATED'
}

​

Error404 -

NOT FOUND

{"error":"Campaign not found - Invalid campaign\_id."}

​

### Add / Update Campaign Webhook

This endpoint add’s a webhook to a campaign or alternatively lets you update a webhook

To

add

a webhook please leave the “id” empty, or as null

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/webhooks?api\_key=${API\_KEY}
--data {"id":217,// set id to null to create a new webhook"name":"Ramesh testing 1","webhook\_url":"https://webhook.site/8222f684-0cf6-43ac-9360-28227fc36d32","event\_types":\["LEAD\_CATEGORY\_UPDATED"\],"categories":\["Interested"\],}

​

The above request yields success/failure response

> Response - <campaign\_webhook>

{"ok":true,"name":"Dinesh Testing lead category webhook","webhook\_url":"https://webhook.site/8222f684-0cf6-43ac-9360-28227fc36d32","email\_campaign\_id":2180,"event\_types":\["LEAD\_CATEGORY\_UPDATED"\],"categories":\["Interested"\],}

​

Error400 -

BAD REQUEST

{"error":"Invalid webhook\_url - {webhookUrl}"}

{"error":"Invalid event\_types - {eachEventType}"}

{"error":"Invalid category - {eachCategory}"}

​

### Delete Campaign Webhook

This endpoint deletes a webhook from a campaign

> API Reference ![🛫](<Base64-Image-Removed>) DELETE

curl https://server.smartlead.ai/api/v1/campaigns/<campaign-id>/webhooks?api\_key=${API\_KEY}
--data {"id":217//webhook ID}

​

The above request yields success/failure response

> Response - <campaign\_webhook>

{"ok":true}

​

### Add Client To System (Whitelabel or not)

This endpoint lets you add new clients to your system

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/client/save?api\_key={API\_KEY}--data {"name":"Ramesh Kumar","email":"ramesh+15@five2one.com.au","permission":\["reply\_master\_inbox"\],"logo":"SmartGen Outreach","logo\_url":null,"password":"Test1234!"}

​

Note\*\*to provide full access permission set

→

"permission": \[ "full\_access" \]

​

The above request yields success/failure response

> Response

{"ok":true,"clientId":299,"name":"Ramesh Kumar","email":"ramesh+15@five2one.com.au","password":"Test1234!"}

​

### Fetch all clients

This endpoint lets you fetch all clients attached to your account

> API Reference ![🛫](<Base64-Image-Removed>) GET

GEThttps://server.smartlead.ai/api/v1/client/?api\_key={API\_KEY}

​

The above request yields success/failure response

> Response

\[{"id":6,"name":"Ramesh Cleint","email":"ramesh+client@five2one.com.au","uuid":"1e19fcb7-6651-444a-8495-e1a4bda16611","created\_at":"2022-08-25T04:24:04.656Z","user\_id":288,"logo":null,"logo\_url":null,"client\_permision":{"permission":\["reply\_master\_inbox"\],"retricted\_category":\[\],}},{"id":298,"name":"Ramesh Kumar","email":"ramesh+14@five2one.com.au","uuid":"d86864b6-c6aa-4ca8-970c-01be63494322","created\_at":"2022-11-25T14:29:04.742Z","user\_id":288,"logo":"SmartGen Outreach","logo\_url":"","client\_permision":{"permission":\["reply\_master\_inbox"\],"retricted\_category":\[\],}}\]

​

### Reconnect failed email accounts

This endpoint lets you bulk reconnect disconnected email accounts.

Rate limited to 3 times in a 24 hour period

> API Reference ![🛫](<Base64-Image-Removed>) POST

curl https://server.smartlead.ai/api/v1/email-accounts/reconnect-failed-email-accounts?api\_key={API\_KEY}--data{}

​

The above request yields success/failure response

> Response

{ ok:true, message: 'Email account(s) added to the queue to reconnect. We will send you an email once completed.' }

​

Error -

NOT\_ACCEPTABLE

{ ok:true, message: 'Bulk reconnect API cannot be consumed more than 3 times a day' }

​

Error -

Not Found

{ ok:true, message: 'No failed email account found!' }

​


---


## Smartlead

**URL:** https://help.smartlead.ai/


[Skip to content](https://help.smartlead.ai/#main)

![🏦 Page icon](<Base64-Image-Removed>)![🏦 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f3e6.svg)

# Smartlead

### ![🚀](<Base64-Image-Removed>) Setup And Kickoff

[![✏️](<Base64-Image-Removed>)\\
\\
Email Account Setup Guides](https://help.smartlead.ai/Email-Account-Setup-Guides-9bad6127275f44caa36668e3d22455a8?pvs=25)

[![🚓](<Base64-Image-Removed>)\\
\\
DMARC, DKIM, SPF & MX Setup](https://help.smartlead.ai/DMARC-DKIM-SPF-MX-Setup-da8b9b155434427f9de8df52a38e88c1?pvs=25)

### ![📨](<Base64-Image-Removed>) Smartlead Guides

[![💰](<Base64-Image-Removed>)\\
\\
Creating a cold email campaign](https://help.smartlead.ai/Creating-a-cold-email-campaign-abfaaa785ecb4254b4ae23ca39d57d2c?pvs=25)

[![🌡️](<Base64-Image-Removed>)\\
\\
Common Email Errors](https://help.smartlead.ai/Common-Email-Errors-9273cbc0ce17483b9479e4c99cf284fa?pvs=25)

[![🚛](<Base64-Image-Removed>)\\
\\
Bulk Add Email Account](https://help.smartlead.ai/Bulk-Add-Email-Account-af48c91fb7584dc398c968831091b389?pvs=25)

[![👥](<Base64-Image-Removed>)\\
\\
Agency View & Client Access](https://help.smartlead.ai/Agency-View-Client-Access-bdc1b09947af483981752eb57b3c6711?pvs=25)

[![🎸](<Base64-Image-Removed>)\\
\\
Lead Categories](https://help.smartlead.ai/Lead-Categories-da81969e563444c28b9e1c100a561ab8?pvs=25)

### ![🎯](<Base64-Image-Removed>) Email Deliverability Best Practices

[![👣](<Base64-Image-Removed>)\\
\\
What is custom domain tracking?](https://help.smartlead.ai/What-is-custom-domain-tracking-38a5fbbd8e6141f488e7a0186fa29f86?pvs=25)

[![🚫](<Base64-Image-Removed>)\\
\\
Global Block List](https://help.smartlead.ai/Global-Block-List-ad2b323a400e46b5a0aad98fcb5d18dd?pvs=25)

[![🌀](<Base64-Image-Removed>)\\
\\
How do you use Spintax?](https://help.smartlead.ai/How-do-you-use-Spintax-d305363b8e564bf7bcba7662a2d6290d?pvs=25)

[![🤑](<Base64-Image-Removed>)\\
\\
AI Email Account Warmups](https://help.smartlead.ai/AI-Email-Account-Warmups-da0451c052184725ad8e3c73f7ee1a82?pvs=25)

![👀](<Base64-Image-Removed>)[DMARC, DKIM & SPF Setup](https://help.smartlead.ai/da8b9b155434427f9de8df52a38e88c1)

### ![🚗](<Base64-Image-Removed>) Roadmap and Feedback

[![🛣️](<Base64-Image-Removed>)\\
\\
Master Roadmap](https://help.smartlead.ai/Master-Roadmap-7824a60083eb423ca6c6105cbff9ede1?pvs=25)

[![🛣️](<Base64-Image-Removed>)\\
\\
Complete Roadmap](https://help.smartlead.ai/b0f93a0712984e0ba5471ed0b23cdf02?v=4435ebd00d194454a6ad3dcb67a1b87f&pvs=25)

### ![✈️](<Base64-Image-Removed>) Automate Your Lead Gen

[![🤖](<Base64-Image-Removed>)\\
\\
API Documentation](https://help.smartlead.ai/API-Documentation-a0d223bdd3154a77b3735497aad9419f?pvs=25)

[![🪝](<Base64-Image-Removed>)\\
\\
Webhook Guide (DEPRECATED)](https://help.smartlead.ai/Webhook-Guide-DEPRECATED-8f10faa000ee4959820cd74c2b8c35f7?pvs=25)

[![📟](<Base64-Image-Removed>)\\
\\
Zapier Setup (beta)](https://help.smartlead.ai/Zapier-Setup-beta-14e16cbeab97415ab7f2927592978bd6?pvs=25)

[![🛻](<Base64-Image-Removed>)\\
\\
Webhook Guide Updated](https://help.smartlead.ai/Webhook-Guide-Updated-4d0ae6b2fa6a4db1b4c1ead824a86866?pvs=25)

### ![💰](<Base64-Image-Removed>)Pipeline Mastery With Cold Email

![🤯](<Base64-Image-Removed>)[Hands-Free Cold Emailing System](https://docs.google.com/document/d/1Z-vvBMp2lQHcBbtiYZgvOMneyN4_YeQwLW8heO5f-qo/edit)

The brute-tested process to building scalable, well reputed outbound emails that land in your leads inbox.

![💵](<Base64-Image-Removed>)[The High Intent Leads System - Purchase Ready Prospects At Scale](https://docs.google.com/document/d/1omOjcl4iV8404bSEsaao6LAmfNkd93MgVWzyoLq0Bi4/edit?usp=sharing)

Find untapped leads ready to spend money to solve their problem with your solution at scale.

![🧾](<Base64-Image-Removed>)[Copywriting Mastery: Frameworks that Convert Cold Email to Meetings](https://docs.google.com/document/d/1WYQDEOnUnebTTM-PHbdO394WpxTAm3nW2ugDmgb15sw/edit#heading=h.kvgb7t94e1pi)

Unleash the best copywriting frameworks and strategies to create offer’s so good your customers will be stupid to say no.

![💰](<Base64-Image-Removed>)[Ultimate Deliverability Engine Checklist](https://docs.google.com/spreadsheets/d/1APy72KAqWt8sDq1yEWkXOiJWBCxEaZyDbun-E7BV5RA/edit#gid=0)

Engineer your emails to always deliver in your leads primary inbox. Tested system to boost deliverability.


---


## Email Account Setup Guides

**URL:** https://help.smartlead.ai/Email-Account-Setup-Guides-9bad6127275f44caa36668e3d22455a8


[Skip to content](https://help.smartlead.ai/Email-Account-Setup-Guides-9bad6127275f44caa36668e3d22455a8#main)

![✏️ Page icon](<Base64-Image-Removed>)![✏️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/270f-fe0f.svg)

# Email Account Setup Guides

[Connect Zoho Mail](https://help.smartlead.ai/Connect-Zoho-Mail-7e1e28c292a74631bc106ee36d0f5731?pvs=25)

[Connect Microsoft Office 365 / Outlook](https://help.smartlead.ai/Connect-Microsoft-Office-365-Outlook-c9fd51c4fe7a470d8b4efaa213e74eae?pvs=25)

[Connect Gmail With SMTP](https://help.smartlead.ai/Connect-Gmail-With-SMTP-f880fd88217741b983e26846d322d6c3?pvs=25)


---


## Timezones

**URL:** https://help.smartlead.ai/Timezones-20fcff9ddbb5441790c7c8e5ce0e9233


[Skip to content](https://help.smartlead.ai/Timezones-20fcff9ddbb5441790c7c8e5ce0e9233#main)

# Timezones

\[\
{\
"value": "Etc/GMT+12",\
"label": "Etc/GMT+12(UTC-12:00)",\
"utc": "UTC-12:00",\
"offset": -12\
},\
{\
"value": "Etc/GMT+11",\
"label": "Etc/GMT+11(UTC-11:00)",\
"utc": "UTC-11:00",\
"offset": -11\
},\
{\
"value": "Pacific/Midway",\
"label": "Pacific/Midway(UTC-11:00)",\
"utc": "UTC-11:00",\
"offset": -11\
},\
{\
"value": "Pacific/Niue",\
"label": "Pacific/Niue(UTC-11:00)",\
"utc": "UTC-11:00",\
"offset": -11\
},\
{\
"value": "Pacific/Pago\_Pago",\
"label": "Pacific/Pago\_Pago(UTC-11:00)",\
"utc": "UTC-11:00",\
"offset": -11\
},\
{\
"value": "Etc/GMT+10",\
"label": "Etc/GMT+10(UTC-10:00)",\
"utc": "UTC-10:00",\
"offset": -10\
},\
{\
"value": "Pacific/Honolulu",\
"label": "Pacific/Honolulu(UTC-10:00)",\
"utc": "UTC-10:00",\
"offset": -10\
},\
{\
"value": "Pacific/Johnston",\
"label": "Pacific/Johnston(UTC-10:00)",\
"utc": "UTC-10:00",\
"offset": -10\
},\
{\
"value": "Pacific/Rarotonga",\
"label": "Pacific/Rarotonga(UTC-10:00)",\
"utc": "UTC-10:00",\
"offset": -10\
},\
{\
"value": "Pacific/Tahiti",\
"label": "Pacific/Tahiti(UTC-10:00)",\
"utc": "UTC-10:00",\
"offset": -10\
},\
{\
"value": "America/Anchorage",\
"label": "America/Anchorage(UTC-09:00)",\
"utc": "UTC-09:00",\
"offset": -8\
},\
{\
"value": "America/Juneau",\
"label": "America/Juneau(UTC-09:00)",\
"utc": "UTC-09:00",\
"offset": -8\
},\
{\
"value": "America/Nome",\
"label": "America/Nome(UTC-09:00)",\
"utc": "UTC-09:00",\
"offset": -8\
},\
{\
"value": "America/Sitka",\
"label": "America/Sitka(UTC-09:00)",\
"utc": "UTC-09:00",\
"offset": -8\
},\
{\
"value": "America/Yakutat",\
"label": "America/Yakutat(UTC-09:00)",\
"utc": "UTC-09:00",\
"offset": -8\
},\
{\
"value": "America/Santa\_Isabel",\
"label": "America/Santa\_Isabel(UTC-08:00)",\
"utc": "UTC-08:00",\
"offset": -7\
},\
{\
"value": "America/Los\_Angeles",\
"label": "America/Los\_Angeles(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Tijuana",\
"label": "America/Tijuana(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Vancouver",\
"label": "America/Vancouver(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Tijuana",\
"label": "America/Tijuana(UTC-08:00)",\
"utc": "UTC-08:00",\
"offset": -8\
},\
{\
"value": "America/Vancouver",\
"label": "America/Vancouver(UTC-08:00)",\
"utc": "UTC-08:00",\
"offset": -8\
},\
{\
"value": "America/Creston",\
"label": "America/Creston(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Dawson",\
"label": "America/Dawson(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Dawson\_Creek",\
"label": "America/Dawson\_Creek(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Hermosillo",\
"label": "America/Hermosillo(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Phoenix",\
"label": "America/Phoenix(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Whitehorse",\
"label": "America/Whitehorse(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "Etc/GMT+7",\
"label": "Etc/GMT+7(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -7\
},\
{\
"value": "America/Chihuahua",\
"label": "America/Chihuahua(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Mazatlan",\
"label": "America/Mazatlan(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Boise",\
"label": "America/Boise(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Cambridge\_Bay",\
"label": "America/Cambridge\_Bay(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Denver",\
"label": "America/Denver(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Edmonton",\
"label": "America/Edmonton(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Inuvik",\
"label": "America/Inuvik(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Ojinaga",\
"label": "America/Ojinaga(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Yellowknife",\
"label": "America/Yellowknife(UTC-07:00)",\
"utc": "UTC-07:00",\
"offset": -6\
},\
{\
"value": "America/Belize",\
"label": "America/Belize(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Costa\_Rica",\
"label": "America/Costa\_Rica(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/El\_Salvador",\
"label": "America/El\_Salvador(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Guatemala",\
"label": "America/Guatemala(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Managua",\
"label": "America/Managua(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Tegucigalpa",\
"label": "America/Tegucigalpa(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "Etc/GMT+6",\
"label": "Etc/GMT+6(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "Pacific/Galapagos",\
"label": "Pacific/Galapagos(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Chicago",\
"label": "America/Chicago(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Indiana/Knox",\
"label": "America/Indiana/Knox(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Indiana/Tell\_City",\
"label": "America/Indiana/Tell\_City(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Matamoros",\
"label": "America/Matamoros(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Menominee",\
"label": "America/Menominee(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/North\_Dakota/Beulah",\
"label": "America/North\_Dakota/Beulah(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/North\_Dakota/Center",\
"label": "America/North\_Dakota/Center(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/North\_Dakota/New\_Salem",\
"label": "America/North\_Dakota/New\_Salem(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Rainy\_River",\
"label": "America/Rainy\_River(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Rankin\_Inlet",\
"label": "America/Rankin\_Inlet(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Resolute",\
"label": "America/Resolute(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Winnipeg",\
"label": "America/Winnipeg(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Bahia\_Banderas",\
"label": "America/Bahia\_Banderas(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Cancun",\
"label": "America/Cancun(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Merida",\
"label": "America/Merida(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Mexico\_City",\
"label": "America/Mexico\_City(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Monterrey",\
"label": "America/Monterrey(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -5\
},\
{\
"value": "America/Regina",\
"label": "America/Regina(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Swift\_Current",\
"label": "America/Swift\_Current(UTC-06:00)",\
"utc": "UTC-06:00",\
"offset": -6\
},\
{\
"value": "America/Bogota",\
"label": "America/Bogota(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Cayman",\
"label": "America/Cayman(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Coral\_Harbour",\
"label": "America/Coral\_Harbour(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Eirunepe",\
"label": "America/Eirunepe(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Guayaquil",\
"label": "America/Guayaquil(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Jamaica",\
"label": "America/Jamaica(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Lima",\
"label": "America/Lima(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Panama",\
"label": "America/Panama(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Rio\_Branco",\
"label": "America/Rio\_Branco(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "Etc/GMT+5",\
"label": "Etc/GMT+5(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Detroit",\
"label": "America/Detroit(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Havana",\
"label": "America/Havana(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Indiana/Petersburg",\
"label": "America/Indiana/Petersburg(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Indiana/Vincennes",\
"label": "America/Indiana/Vincennes(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Indiana/Winamac",\
"label": "America/Indiana/Winamac(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Iqaluit",\
"label": "America/Iqaluit(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Kentucky/Monticello",\
"label": "America/Kentucky/Monticello(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Louisville",\
"label": "America/Louisville(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Montreal",\
"label": "America/Montreal(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Nassau",\
"label": "America/Nassau(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/New\_York",\
"label": "America/New\_York(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Nipigon",\
"label": "America/Nipigon(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Pangnirtung",\
"label": "America/Pangnirtung(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Port-au-Prince",\
"label": "America/Port-au-Prince(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Thunder\_Bay",\
"label": "America/Thunder\_Bay(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Toronto",\
"label": "America/Toronto(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Detroit",\
"label": "America/Detroit(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Havana",\
"label": "America/Havana(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Indiana/Petersburg",\
"label": "America/Indiana/Petersburg(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Indiana/Vincennes",\
"label": "America/Indiana/Vincennes(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Indiana/Winamac",\
"label": "America/Indiana/Winamac(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Iqaluit",\
"label": "America/Iqaluit(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Kentucky/Monticello",\
"label": "America/Kentucky/Monticello(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Louisville",\
"label": "America/Louisville(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Montreal",\
"label": "America/Montreal(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Nassau",\
"label": "America/Nassau(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/New\_York",\
"label": "America/New\_York(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Nipigon",\
"label": "America/Nipigon(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Pangnirtung",\
"label": "America/Pangnirtung(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Port-au-Prince",\
"label": "America/Port-au-Prince(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Thunder\_Bay",\
"label": "America/Thunder\_Bay(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Toronto",\
"label": "America/Toronto(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Indiana/Marengo",\
"label": "America/Indiana/Marengo(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Indiana/Vevay",\
"label": "America/Indiana/Vevay(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Indianapolis",\
"label": "America/Indianapolis(UTC-05:00)",\
"utc": "UTC-05:00",\
"offset": -5\
},\
{\
"value": "America/Caracas",\
"label": "America/Caracas(UTC-04:30)",\
"utc": "UTC-04:30",\
"offset": -4.5\
},\
{\
"value": "America/Asuncion",\
"label": "America/Asuncion(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Glace\_Bay",\
"label": "America/Glace\_Bay(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -3\
},\
{\
"value": "America/Goose\_Bay",\
"label": "America/Goose\_Bay(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -3\
},\
{\
"value": "America/Halifax",\
"label": "America/Halifax(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -3\
},\
{\
"value": "America/Moncton",\
"label": "America/Moncton(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -3\
},\
{\
"value": "America/Thule",\
"label": "America/Thule(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -3\
},\
{\
"value": "Atlantic/Bermuda",\
"label": "Atlantic/Bermuda(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -3\
},\
{\
"value": "America/Campo\_Grande",\
"label": "America/Campo\_Grande(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Cuiaba",\
"label": "America/Cuiaba(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Anguilla",\
"label": "America/Anguilla(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Antigua",\
"label": "America/Antigua(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Aruba",\
"label": "America/Aruba(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Barbados",\
"label": "America/Barbados(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Blanc-Sablon",\
"label": "America/Blanc-Sablon(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Boa\_Vista",\
"label": "America/Boa\_Vista(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Curacao",\
"label": "America/Curacao(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Dominica",\
"label": "America/Dominica(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Grand\_Turk",\
"label": "America/Grand\_Turk(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Grenada",\
"label": "America/Grenada(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Guadeloupe",\
"label": "America/Guadeloupe(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Guyana",\
"label": "America/Guyana(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Kralendijk",\
"label": "America/Kralendijk(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/La\_Paz",\
"label": "America/La\_Paz(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Lower\_Princes",\
"label": "America/Lower\_Princes(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Manaus",\
"label": "America/Manaus(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Marigot",\
"label": "America/Marigot(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Martinique",\
"label": "America/Martinique(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Montserrat",\
"label": "America/Montserrat(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Port\_of\_Spain",\
"label": "America/Port\_of\_Spain(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Porto\_Velho",\
"label": "America/Porto\_Velho(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Puerto\_Rico",\
"label": "America/Puerto\_Rico(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Santo\_Domingo",\
"label": "America/Santo\_Domingo(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/St\_Barthelemy",\
"label": "America/St\_Barthelemy(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/St\_Kitts",\
"label": "America/St\_Kitts(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/St\_Lucia",\
"label": "America/St\_Lucia(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/St\_Thomas",\
"label": "America/St\_Thomas(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/St\_Vincent",\
"label": "America/St\_Vincent(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Tortola",\
"label": "America/Tortola(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "Etc/GMT+4",\
"label": "Etc/GMT+4(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/Santiago",\
"label": "America/Santiago(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "Antarctica/Palmer",\
"label": "Antarctica/Palmer(UTC-04:00)",\
"utc": "UTC-04:00",\
"offset": -4\
},\
{\
"value": "America/St\_Johns",\
"label": "America/St\_Johns(UTC-03:30)",\
"utc": "UTC-03:30",\
"offset": -2.5\
},\
{\
"value": "America/Sao\_Paulo",\
"label": "America/Sao\_Paulo(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/La\_Rioja",\
"label": "America/Argentina/La\_Rioja(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/Rio\_Gallegos",\
"label": "America/Argentina/Rio\_Gallegos(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/Salta",\
"label": "America/Argentina/Salta(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/San\_Juan",\
"label": "America/Argentina/San\_Juan(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/San\_Luis",\
"label": "America/Argentina/San\_Luis(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/Tucuman",\
"label": "America/Argentina/Tucuman(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Argentina/Ushuaia",\
"label": "America/Argentina/Ushuaia(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Buenos\_Aires",\
"label": "America/Buenos\_Aires(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Catamarca",\
"label": "America/Catamarca(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Cordoba",\
"label": "America/Cordoba(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Jujuy",\
"label": "America/Jujuy(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Mendoza",\
"label": "America/Mendoza(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Araguaina",\
"label": "America/Araguaina(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Belem",\
"label": "America/Belem(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Cayenne",\
"label": "America/Cayenne(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Fortaleza",\
"label": "America/Fortaleza(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Maceio",\
"label": "America/Maceio(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Paramaribo",\
"label": "America/Paramaribo(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Recife",\
"label": "America/Recife(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Santarem",\
"label": "America/Santarem(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "Antarctica/Rothera",\
"label": "Antarctica/Rothera(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "Atlantic/Stanley",\
"label": "Atlantic/Stanley(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "Etc/GMT+3",\
"label": "Etc/GMT+3(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Godthab",\
"label": "America/Godthab(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Montevideo",\
"label": "America/Montevideo(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Bahia",\
"label": "America/Bahia(UTC-03:00)",\
"utc": "UTC-03:00",\
"offset": -3\
},\
{\
"value": "America/Noronha",\
"label": "America/Noronha(UTC-02:00)",\
"utc": "UTC-02:00",\
"offset": -2\
},\
{\
"value": "Atlantic/South\_Georgia",\
"label": "Atlantic/South\_Georgia(UTC-02:00)",\
"utc": "UTC-02:00",\
"offset": -2\
},\
{\
"value": "Etc/GMT+2",\
"label": "Etc/GMT+2(UTC-02:00)",\
"utc": "UTC-02:00",\
"offset": -2\
},\
{\
"value": "America/Scoresbysund",\
"label": "America/Scoresbysund(UTC-01:00)",\
"utc": "UTC-01:00",\
"offset": 0\
},\
{\
"value": "Atlantic/Azores",\
"label": "Atlantic/Azores(UTC-01:00)",\
"utc": "UTC-01:00",\
"offset": 0\
},\
{\
"value": "Atlantic/Cape\_Verde",\
"label": "Atlantic/Cape\_Verde(UTC-01:00)",\
"utc": "UTC-01:00",\
"offset": -1\
},\
{\
"value": "Etc/GMT+1",\
"label": "Etc/GMT+1(UTC-01:00)",\
"utc": "UTC-01:00",\
"offset": -1\
},\
{\
"value": "Africa/Casablanca",\
"label": "Africa/Casablanca(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "Africa/El\_Aaiun",\
"label": "Africa/El\_Aaiun(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "America/Danmarkshavn",\
"label": "America/Danmarkshavn(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Etc/GMT",\
"label": "Etc/GMT(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Europe/Isle\_of\_Man",\
"label": "Europe/Isle\_of\_Man(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Europe/Guernsey",\
"label": "Europe/Guernsey(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Europe/Jersey",\
"label": "Europe/Jersey(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Europe/London",\
"label": "Europe/London(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Europe/Isle\_of\_Man",\
"label": "Europe/Isle\_of\_Man(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Europe/Guernsey",\
"label": "Europe/Guernsey(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Europe/Jersey",\
"label": "Europe/Jersey(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Europe/London",\
"label": "Europe/London(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Atlantic/Canary",\
"label": "Atlantic/Canary(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "Atlantic/Faeroe",\
"label": "Atlantic/Faeroe(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "Atlantic/Madeira",\
"label": "Atlantic/Madeira(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "Europe/Dublin",\
"label": "Europe/Dublin(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "Europe/Lisbon",\
"label": "Europe/Lisbon(UTC)",\
"utc": "UTC",\
"offset": 1\
},\
{\
"value": "Africa/Abidjan",\
"label": "Africa/Abidjan(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Accra",\
"label": "Africa/Accra(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Bamako",\
"label": "Africa/Bamako(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Banjul",\
"label": "Africa/Banjul(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Bissau",\
"label": "Africa/Bissau(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Conakry",\
"label": "Africa/Conakry(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Dakar",\
"label": "Africa/Dakar(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Freetown",\
"label": "Africa/Freetown(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Lome",\
"label": "Africa/Lome(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Monrovia",\
"label": "Africa/Monrovia(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Nouakchott",\
"label": "Africa/Nouakchott(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Ouagadougou",\
"label": "Africa/Ouagadougou(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Africa/Sao\_Tome",\
"label": "Africa/Sao\_Tome(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Atlantic/Reykjavik",\
"label": "Atlantic/Reykjavik(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Atlantic/St\_Helena",\
"label": "Atlantic/St\_Helena(UTC)",\
"utc": "UTC",\
"offset": 0\
},\
{\
"value": "Arctic/Longyearbyen",\
"label": "Arctic/Longyearbyen(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Amsterdam",\
"label": "Europe/Amsterdam(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Andorra",\
"label": "Europe/Andorra(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Berlin",\
"label": "Europe/Berlin(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Busingen",\
"label": "Europe/Busingen(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Gibraltar",\
"label": "Europe/Gibraltar(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Luxembourg",\
"label": "Europe/Luxembourg(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Malta",\
"label": "Europe/Malta(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Monaco",\
"label": "Europe/Monaco(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Oslo",\
"label": "Europe/Oslo(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Rome",\
"label": "Europe/Rome(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/San\_Marino",\
"label": "Europe/San\_Marino(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Stockholm",\
"label": "Europe/Stockholm(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Vaduz",\
"label": "Europe/Vaduz(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Vatican",\
"label": "Europe/Vatican(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Vienna",\
"label": "Europe/Vienna(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Zurich",\
"label": "Europe/Zurich(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Belgrade",\
"label": "Europe/Belgrade(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Bratislava",\
"label": "Europe/Bratislava(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Budapest",\
"label": "Europe/Budapest(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Ljubljana",\
"label": "Europe/Ljubljana(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Podgorica",\
"label": "Europe/Podgorica(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Prague",\
"label": "Europe/Prague(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Tirane",\
"label": "Europe/Tirane(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Africa/Ceuta",\
"label": "Africa/Ceuta(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Brussels",\
"label": "Europe/Brussels(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Copenhagen",\
"label": "Europe/Copenhagen(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Madrid",\
"label": "Europe/Madrid(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Paris",\
"label": "Europe/Paris(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Sarajevo",\
"label": "Europe/Sarajevo(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Skopje",\
"label": "Europe/Skopje(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Warsaw",\
"label": "Europe/Warsaw(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Europe/Zagreb",\
"label": "Europe/Zagreb(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 2\
},\
{\
"value": "Africa/Algiers",\
"label": "Africa/Algiers(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Bangui",\
"label": "Africa/Bangui(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Brazzaville",\
"label": "Africa/Brazzaville(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Douala",\
"label": "Africa/Douala(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Kinshasa",\
"label": "Africa/Kinshasa(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Lagos",\
"label": "Africa/Lagos(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Libreville",\
"label": "Africa/Libreville(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Luanda",\
"label": "Africa/Luanda(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Malabo",\
"label": "Africa/Malabo(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Ndjamena",\
"label": "Africa/Ndjamena(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Niamey",\
"label": "Africa/Niamey(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Porto-Novo",\
"label": "Africa/Porto-Novo(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Tunis",\
"label": "Africa/Tunis(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Etc/GMT-1",\
"label": "Etc/GMT-1(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Africa/Windhoek",\
"label": "Africa/Windhoek(UTC+01:00)",\
"utc": "UTC+01:00",\
"offset": 1\
},\
{\
"value": "Asia/Nicosia",\
"label": "Asia/Nicosia(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Athens",\
"label": "Europe/Athens(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Bucharest",\
"label": "Europe/Bucharest(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Chisinau",\
"label": "Europe/Chisinau(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Asia/Beirut",\
"label": "Asia/Beirut(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Africa/Cairo",\
"label": "Africa/Cairo(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Asia/Damascus",\
"label": "Asia/Damascus(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Asia/Nicosia",\
"label": "Asia/Nicosia(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Athens",\
"label": "Europe/Athens(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Bucharest",\
"label": "Europe/Bucharest(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Chisinau",\
"label": "Europe/Chisinau(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Helsinki",\
"label": "Europe/Helsinki(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Kiev",\
"label": "Europe/Kiev(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Mariehamn",\
"label": "Europe/Mariehamn(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Nicosia",\
"label": "Europe/Nicosia(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Riga",\
"label": "Europe/Riga(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Sofia",\
"label": "Europe/Sofia(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Tallinn",\
"label": "Europe/Tallinn(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Uzhgorod",\
"label": "Europe/Uzhgorod(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Vilnius",\
"label": "Europe/Vilnius(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Zaporozhye",\
"label": "Europe/Zaporozhye(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Africa/Blantyre",\
"label": "Africa/Blantyre(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Bujumbura",\
"label": "Africa/Bujumbura(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Gaborone",\
"label": "Africa/Gaborone(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Harare",\
"label": "Africa/Harare(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Johannesburg",\
"label": "Africa/Johannesburg(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Kigali",\
"label": "Africa/Kigali(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Lubumbashi",\
"label": "Africa/Lubumbashi(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Lusaka",\
"label": "Africa/Lusaka(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Maputo",\
"label": "Africa/Maputo(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Maseru",\
"label": "Africa/Maseru(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Africa/Mbabane",\
"label": "Africa/Mbabane(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Etc/GMT-2",\
"label": "Etc/GMT-2(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Europe/Helsinki",\
"label": "Europe/Helsinki(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Kiev",\
"label": "Europe/Kiev(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Mariehamn",\
"label": "Europe/Mariehamn(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Riga",\
"label": "Europe/Riga(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Sofia",\
"label": "Europe/Sofia(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Tallinn",\
"label": "Europe/Tallinn(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Uzhgorod",\
"label": "Europe/Uzhgorod(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Vilnius",\
"label": "Europe/Vilnius(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Zaporozhye",\
"label": "Europe/Zaporozhye(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Europe/Istanbul",\
"label": "Europe/Istanbul(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Asia/Jerusalem",\
"label": "Asia/Jerusalem(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Africa/Tripoli",\
"label": "Africa/Tripoli(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 2\
},\
{\
"value": "Asia/Amman",\
"label": "Asia/Amman(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Asia/Baghdad",\
"label": "Asia/Baghdad(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Kaliningrad",\
"label": "Europe/Kaliningrad(UTC+02:00)",\
"utc": "UTC+02:00",\
"offset": 3\
},\
{\
"value": "Asia/Aden",\
"label": "Asia/Aden(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Asia/Bahrain",\
"label": "Asia/Bahrain(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Asia/Kuwait",\
"label": "Asia/Kuwait(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Asia/Qatar",\
"label": "Asia/Qatar(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Asia/Riyadh",\
"label": "Asia/Riyadh(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Addis\_Ababa",\
"label": "Africa/Addis\_Ababa(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Asmera",\
"label": "Africa/Asmera(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Dar\_es\_Salaam",\
"label": "Africa/Dar\_es\_Salaam(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Djibouti",\
"label": "Africa/Djibouti(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Juba",\
"label": "Africa/Juba(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Kampala",\
"label": "Africa/Kampala(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Khartoum",\
"label": "Africa/Khartoum(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Mogadishu",\
"label": "Africa/Mogadishu(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Africa/Nairobi",\
"label": "Africa/Nairobi(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Antarctica/Syowa",\
"label": "Antarctica/Syowa(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Etc/GMT-3",\
"label": "Etc/GMT-3(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Indian/Antananarivo",\
"label": "Indian/Antananarivo(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Indian/Comoro",\
"label": "Indian/Comoro(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Indian/Mayotte",\
"label": "Indian/Mayotte(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Kirov",\
"label": "Europe/Kirov(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Moscow",\
"label": "Europe/Moscow(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Simferopol",\
"label": "Europe/Simferopol(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Volgograd",\
"label": "Europe/Volgograd(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Minsk",\
"label": "Europe/Minsk(UTC+03:00)",\
"utc": "UTC+03:00",\
"offset": 3\
},\
{\
"value": "Europe/Astrakhan",\
"label": "Europe/Astrakhan(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Europe/Samara",\
"label": "Europe/Samara(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Europe/Ulyanovsk",\
"label": "Europe/Ulyanovsk(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Asia/Tehran",\
"label": "Asia/Tehran(UTC+03:30)",\
"utc": "UTC+03:30",\
"offset": 4.5\
},\
{\
"value": "Asia/Dubai",\
"label": "Asia/Dubai(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Asia/Muscat",\
"label": "Asia/Muscat(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Etc/GMT-4",\
"label": "Etc/GMT-4(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Asia/Baku",\
"label": "Asia/Baku(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 5\
},\
{\
"value": "Indian/Mahe",\
"label": "Indian/Mahe(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Indian/Mauritius",\
"label": "Indian/Mauritius(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Indian/Reunion",\
"label": "Indian/Reunion(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Asia/Tbilisi",\
"label": "Asia/Tbilisi(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Asia/Yerevan",\
"label": "Asia/Yerevan(UTC+04:00)",\
"utc": "UTC+04:00",\
"offset": 4\
},\
{\
"value": "Asia/Kabul",\
"label": "Asia/Kabul(UTC+04:30)",\
"utc": "UTC+04:30",\
"offset": 4.5\
},\
{\
"value": "Antarctica/Mawson",\
"label": "Antarctica/Mawson(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Aqtau",\
"label": "Asia/Aqtau(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Aqtobe",\
"label": "Asia/Aqtobe(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Ashgabat",\
"label": "Asia/Ashgabat(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Dushanbe",\
"label": "Asia/Dushanbe(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Oral",\
"label": "Asia/Oral(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Samarkand",\
"label": "Asia/Samarkand(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Tashkent",\
"label": "Asia/Tashkent(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Etc/GMT-5",\
"label": "Etc/GMT-5(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Indian/Kerguelen",\
"label": "Indian/Kerguelen(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Indian/Maldives",\
"label": "Indian/Maldives(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Yekaterinburg",\
"label": "Asia/Yekaterinburg(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Karachi",\
"label": "Asia/Karachi(UTC+05:00)",\
"utc": "UTC+05:00",\
"offset": 5\
},\
{\
"value": "Asia/Kolkata",\
"label": "Asia/Kolkata(UTC+05:30)",\
"utc": "UTC+05:30",\
"offset": 5.5\
},\
{\
"value": "Asia/Calcutta",\
"label": "Asia/Calcutta(UTC+05:30)",\
"utc": "UTC+05:30",\
"offset": 5.5\
},\
{\
"value": "Asia/Colombo",\
"label": "Asia/Colombo(UTC+05:30)",\
"utc": "UTC+05:30",\
"offset": 5.5\
},\
{\
"value": "Asia/Kathmandu",\
"label": "Asia/Kathmandu(UTC+05:45)",\
"utc": "UTC+05:45",\
"offset": 5.75\
},\
{\
"value": "Antarctica/Vostok",\
"label": "Antarctica/Vostok(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Almaty",\
"label": "Asia/Almaty(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Bishkek",\
"label": "Asia/Bishkek(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Qyzylorda",\
"label": "Asia/Qyzylorda(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Urumqi",\
"label": "Asia/Urumqi(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Etc/GMT-6",\
"label": "Etc/GMT-6(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Indian/Chagos",\
"label": "Indian/Chagos(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Dhaka",\
"label": "Asia/Dhaka(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Thimphu",\
"label": "Asia/Thimphu(UTC+06:00)",\
"utc": "UTC+06:00",\
"offset": 6\
},\
{\
"value": "Asia/Rangoon",\
"label": "Asia/Rangoon(UTC+06:30)",\
"utc": "UTC+06:30",\
"offset": 6.5\
},\
{\
"value": "Indian/Cocos",\
"label": "Indian/Cocos(UTC+06:30)",\
"utc": "UTC+06:30",\
"offset": 6.5\
},\
{\
"value": "Antarctica/Davis",\
"label": "Antarctica/Davis(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Bangkok",\
"label": "Asia/Bangkok(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Hovd",\
"label": "Asia/Hovd(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Jakarta",\
"label": "Asia/Jakarta(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Phnom\_Penh",\
"label": "Asia/Phnom\_Penh(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Pontianak",\
"label": "Asia/Pontianak(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Saigon",\
"label": "Asia/Saigon(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Vientiane",\
"label": "Asia/Vientiane(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Etc/GMT-7",\
"label": "Etc/GMT-7(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Indian/Christmas",\
"label": "Indian/Christmas(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Novokuznetsk",\
"label": "Asia/Novokuznetsk(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Novosibirsk",\
"label": "Asia/Novosibirsk(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Omsk",\
"label": "Asia/Omsk(UTC+07:00)",\
"utc": "UTC+07:00",\
"offset": 7\
},\
{\
"value": "Asia/Hong\_Kong",\
"label": "Asia/Hong\_Kong(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Macau",\
"label": "Asia/Macau(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Shanghai",\
"label": "Asia/Shanghai(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Krasnoyarsk",\
"label": "Asia/Krasnoyarsk(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Brunei",\
"label": "Asia/Brunei(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Kuala\_Lumpur",\
"label": "Asia/Kuala\_Lumpur(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Kuching",\
"label": "Asia/Kuching(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Makassar",\
"label": "Asia/Makassar(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Manila",\
"label": "Asia/Manila(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Singapore",\
"label": "Asia/Singapore(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Etc/GMT-8",\
"label": "Etc/GMT-8(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Antarctica/Casey",\
"label": "Antarctica/Casey(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Australia/Perth",\
"label": "Australia/Perth(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Taipei",\
"label": "Asia/Taipei(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Choibalsan",\
"label": "Asia/Choibalsan(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Ulaanbaatar",\
"label": "Asia/Ulaanbaatar(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Irkutsk",\
"label": "Asia/Irkutsk(UTC+08:00)",\
"utc": "UTC+08:00",\
"offset": 8\
},\
{\
"value": "Asia/Dili",\
"label": "Asia/Dili(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Asia/Jayapura",\
"label": "Asia/Jayapura(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Asia/Tokyo",\
"label": "Asia/Tokyo(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Etc/GMT-9",\
"label": "Etc/GMT-9(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Pacific/Palau",\
"label": "Pacific/Palau(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Asia/Pyongyang",\
"label": "Asia/Pyongyang(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Asia/Seoul",\
"label": "Asia/Seoul(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Australia/Adelaide",\
"label": "Australia/Adelaide(UTC+09:30)",\
"utc": "UTC+09:30",\
"offset": 9.5\
},\
{\
"value": "Australia/Broken\_Hill",\
"label": "Australia/Broken\_Hill(UTC+09:30)",\
"utc": "UTC+09:30",\
"offset": 9.5\
},\
{\
"value": "Australia/Darwin",\
"label": "Australia/Darwin(UTC+09:30)",\
"utc": "UTC+09:30",\
"offset": 9.5\
},\
{\
"value": "Australia/Brisbane",\
"label": "Australia/Brisbane(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Australia/Lindeman",\
"label": "Australia/Lindeman(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Australia/Melbourne",\
"label": "Australia/Melbourne(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Australia/Sydney",\
"label": "Australia/Sydney(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Antarctica/DumontDUrville",\
"label": "Antarctica/DumontDUrville(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Etc/GMT-10",\
"label": "Etc/GMT-10(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Pacific/Guam",\
"label": "Pacific/Guam(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Pacific/Port\_Moresby",\
"label": "Pacific/Port\_Moresby(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Pacific/Saipan",\
"label": "Pacific/Saipan(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Pacific/Truk",\
"label": "Pacific/Truk(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Australia/Currie",\
"label": "Australia/Currie(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Australia/Hobart",\
"label": "Australia/Hobart(UTC+10:00)",\
"utc": "UTC+10:00",\
"offset": 10\
},\
{\
"value": "Asia/Chita",\
"label": "Asia/Chita(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Asia/Khandyga",\
"label": "Asia/Khandyga(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Asia/Yakutsk",\
"label": "Asia/Yakutsk(UTC+09:00)",\
"utc": "UTC+09:00",\
"offset": 9\
},\
{\
"value": "Antarctica/Macquarie",\
"label": "Antarctica/Macquarie(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Etc/GMT-11",\
"label": "Etc/GMT-11(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Pacific/Efate",\
"label": "Pacific/Efate(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Pacific/Guadalcanal",\
"label": "Pacific/Guadalcanal(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Pacific/Kosrae",\
"label": "Pacific/Kosrae(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Pacific/Noumea",\
"label": "Pacific/Noumea(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Pacific/Ponape",\
"label": "Pacific/Ponape(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Asia/Sakhalin",\
"label": "Asia/Sakhalin(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Asia/Ust-Nera",\
"label": "Asia/Ust-Nera(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Asia/Vladivostok",\
"label": "Asia/Vladivostok(UTC+11:00)",\
"utc": "UTC+11:00",\
"offset": 11\
},\
{\
"value": "Antarctica/McMurdo",\
"label": "Antarctica/McMurdo(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Auckland",\
"label": "Pacific/Auckland(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Etc/GMT-12",\
"label": "Etc/GMT-12(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Funafuti",\
"label": "Pacific/Funafuti(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Kwajalein",\
"label": "Pacific/Kwajalein(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Majuro",\
"label": "Pacific/Majuro(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Nauru",\
"label": "Pacific/Nauru(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Tarawa",\
"label": "Pacific/Tarawa(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Wake",\
"label": "Pacific/Wake(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Wallis",\
"label": "Pacific/Wallis(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Pacific/Fiji",\
"label": "Pacific/Fiji(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Asia/Anadyr",\
"label": "Asia/Anadyr(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Asia/Kamchatka",\
"label": "Asia/Kamchatka(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Asia/Magadan",\
"label": "Asia/Magadan(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Asia/Srednekolymsk",\
"label": "Asia/Srednekolymsk(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 12\
},\
{\
"value": "Asia/Kamchatka",\
"label": "Asia/Kamchatka(UTC+12:00)",\
"utc": "UTC+12:00",\
"offset": 13\
},\
{\
"value": "Etc/GMT-13",\
"label": "Etc/GMT-13(UTC+13:00)",\
"utc": "UTC+13:00",\
"offset": 13\
},\
{\
"value": "Pacific/Enderbury",\
"label": "Pacific/Enderbury(UTC+13:00)",\
"utc": "UTC+13:00",\
"offset": 13\
},\
{\
"value": "Pacific/Fakaofo",\
"label": "Pacific/Fakaofo(UTC+13:00)",\
"utc": "UTC+13:00",\
"offset": 13\
},\
{\
"value": "Pacific/Tongatapu",\
"label": "Pacific/Tongatapu(UTC+13:00)",\
"utc": "UTC+13:00",\
"offset": 13\
},\
{\
"value": "Pacific/Apia",\
"label": "Pacific/Apia(UTC+13:00)",\
"utc": "UTC+13:00",\
"offset": 13\
}\
\]

​


---


## DMARC, DKIM, SPF & MX Setup

**URL:** https://help.smartlead.ai/DMARC-DKIM-SPF-MX-Setup-da8b9b155434427f9de8df52a38e88c1


[Skip to content](https://help.smartlead.ai/DMARC-DKIM-SPF-MX-Setup-da8b9b155434427f9de8df52a38e88c1#main)

![🚓 Page icon](<Base64-Image-Removed>)![🚓 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f693.svg)

# DMARC, DKIM, SPF & MX Setup

Confusing at first, these abbreviations are going to play a very important role in ensuring your well crafted email lands in your leads inbox!

So let’s take a quick dive into what these actually are and why you need to bother about them. If you get all the below 4 done right, you drastically improve your chance of landing in your leads main inbox.

DKIM

This is an authentication method that lets Email Service Providers know if the email is actually associated to the domain. AKA no random person can send an email on behalf of a facebook employee or mark@facebook.com

SPF

Each email is given a “Made in” tag, similar to groceries you buy. Lets say you only buy cheese from farms in New Zealand. Next time you buy a cheese block you’d look up to see if the farm it’s made in, is from New Zealand, and if not you’d reject it. Similarly so, this policy is used by the receiving email provider to look at the “Made in IP address” to see if it was actually made by [facebook.com](http://facebook.com/)’s IP (for.eg) and not some other IP.

DMARC

This policy uses both DKIM and SPF listed above to decide whether the received email should land up in junk or be straight out rejected. It basically lets every email service provider know that the email you’ve sent is legitimate and sent by you.

MX Records

In short, these records tell the internet which server is responsible for accepting emails when emails are sent to your domain. Hence the name Mail Exchange Servers

Here’s how you can set each of them up:

#### MX Records

Without MX records you won’t be able receive or even send emails. This part is fundamental.

Gmail [MX Record Setup](https://apps.google.com/supportwidget/articlehome?hl=en&article_url=https%3A%2F%2Fsupport.google.com%2Fa%2Fanswer%2F33915%3Fhl%3Den&product_context=33915&product_name=UnuFlow&trigger_context=a)

Zoho [MX Record Setup](https://www.zoho.com/mail/help/adminconsole/configure-email-delivery.html)

Outlook [MX Record Setup](https://docs.microsoft.com/en-us/microsoft-365/admin/get-help-with-domains/create-dns-records-at-any-dns-hosting-provider?view=o365-worldwide)

#### DKIM Setup

Gmail [setup](https://apps.google.com/supportwidget/articlehome?hl=en&article_url=https%3A%2F%2Fsupport.google.com%2Fa%2Fanswer%2F180504%3Fhl%3Den&product_context=180504&product_name=UnuFlow&trigger_context=a)

Zoho [setup](https://www.zoho.com/mail/help/adminconsole/dkim-configuration.html)

Outlook [setup](https://docs.microsoft.com/en-us/microsoft-365/security/office-365-security/use-dkim-to-validate-outbound-email?view=o365-worldwide)

#### SPF Setup

Gmail [setup](https://apps.google.com/supportwidget/articlehome?hl=en&article_url=https%3A%2F%2Fsupport.google.com%2Fa%2Fanswer%2F10684623%3Fhl%3Den&product_context=10684623&product_name=UnuFlow&trigger_context=a)

Zoho [setup](https://www.zoho.com/mail/help/adminconsole/spf-configuration.html)

Outlook [setup](https://docs.microsoft.com/en-us/microsoft-365/security/office-365-security/set-up-spf-in-office-365-to-help-prevent-spoofing?view=o365-worldwide)

#### DMARC Setup

Gmail [setup](https://apps.google.com/supportwidget/articlehome?hl=en&article_url=https%3A%2F%2Fsupport.google.com%2Fa%2Fanswer%2F2466563%3Fhl%3Den&product_context=2466563&product_name=UnuFlow&trigger_context=a)

Before you do the setup, read [this](https://apps.google.com/supportwidget/articlehome?hl=en&article_url=https%3A%2F%2Fsupport.google.com%2Fa%2Fanswer%2F10032674%3Fhl%3Den&product_context=10032674&product_name=UnuFlow&trigger_context=a)

Zoho [setup](https://www.zoho.com/mail/help/adminconsole/dmarc-policy.html)

Outlook [setup](https://dmarcly.com/blog/how-to-set-up-dmarc-dkim-and-spf-in-office-365-o365-the-complete-implementation-guide)


---


## Master Roadmap

**URL:** https://help.smartlead.ai/Master-Roadmap-7824a60083eb423ca6c6105cbff9ede1


[Skip to content](https://help.smartlead.ai/Master-Roadmap-7824a60083eb423ca6c6105cbff9ede1#main)

![🛣️ Page icon](<Base64-Image-Removed>)![🛣️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f6e3-fe0f.svg)

# Master Roadmap

Upcoming view

Complete view

![⏰](<Base64-Image-Removed>)

Scheduled reminders from Master Inbox

![🎯](<Base64-Image-Removed>) Multi Channel Outreach

![💻](<Base64-Image-Removed>) Dedicated IP access

![🖼️](<Base64-Image-Removed>)

Image Personalisation

![💼](<Base64-Image-Removed>)

Custom CRM

![🎍](<Base64-Image-Removed>)

Account Wide Global Analytics

![🏏](<Base64-Image-Removed>)

Native CRM Integrations

![🪐](<Base64-Image-Removed>)

Global lead list management

![🏜️](<Base64-Image-Removed>)

Whitelabel Clients Given Credits

October

November

December

January

February

March

April

May

June

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

11

January 2026

Month

Today

Name

![⏰](<Base64-Image-Removed>)

Scheduled reminders from Master Inbox

![🎯](<Base64-Image-Removed>) Multi Channel Outreach

![💻](<Base64-Image-Removed>) Dedicated IP access

![🖼️](<Base64-Image-Removed>)

Image Personalisation

![💼](<Base64-Image-Removed>)

Custom CRM

![🎍](<Base64-Image-Removed>)

Account Wide Global Analytics

![🏏](<Base64-Image-Removed>)

Native CRM Integrations

![🪐](<Base64-Image-Removed>)

Global lead list management

![🏜️](<Base64-Image-Removed>)

Whitelabel Clients Given Credits

![🌦️](<Base64-Image-Removed>)

Calendar Freeze Time

![🛶](<Base64-Image-Removed>)

Conditional Follow up Messages

![👀](<Base64-Image-Removed>)

Video Personalisation At Scale

![🤫](<Base64-Image-Removed>)

Chrome Extension

![✅ Callout icon](<Base64-Image-Removed>)

Completed and Live Features ![⬇️](<Base64-Image-Removed>)​

![🎯](<Base64-Image-Removed>) Multiple Categories to count for positive replies

![🎯](<Base64-Image-Removed>) Out of Office Sentiment Analyser + Ignore OOO Reply metrics

![🎯](<Base64-Image-Removed>) Email Service Provider Matching

![🎯](<Base64-Image-Removed>) Gmail oAuth

![🎯](<Base64-Image-Removed>)[Email Warm up](https://help.smartlead.ai/da0451c052184725ad8e3c73f7ee1a82)

![🎯](<Base64-Image-Removed>)[Spintax](https://help.smartlead.ai/d305363b8e564bf7bcba7662a2d6290d)

![🎯](<Base64-Image-Removed>)[Webhooks](https://help.smartlead.ai/8f10faa000ee4959820cd74c2b8c35f7)

![🎯](<Base64-Image-Removed>)[Images In HTML](https://feedback.smartlead.ai/announcements/images-in-html)

![🎯](<Base64-Image-Removed>)[Global Block List](https://help.smartlead.ai/ad2b323a400e46b5a0aad98fcb5d18dd)

![🎯](<Base64-Image-Removed>) Agency view (Beta)

![🎯](<Base64-Image-Removed>) Master Inbox Reply Management

![🎯](<Base64-Image-Removed>) Email Writing Assistant + Spam Detector

![🎯](<Base64-Image-Removed>) Bounce Detection

![🎯](<Base64-Image-Removed>) Rich Text Editor

![🎯](<Base64-Image-Removed>)[Custom Domain Tracking](https://help.smartlead.ai/38a5fbbd8e6141f488e7a0186fa29f86)

![🎯](<Base64-Image-Removed>) Unsubscribe Links

![🎯](<Base64-Image-Removed>) Duplicate Campaigns

![🎯](<Base64-Image-Removed>) Master Inbox

![🎯](<Base64-Image-Removed>) Personalisation

![🎯](<Base64-Image-Removed>) Open and Link Click Tracking

![🎯](<Base64-Image-Removed>) Multiple Inboxes

![🎯](<Base64-Image-Removed>) Campaign Stats

![🎯](<Base64-Image-Removed>) Auto Follow-ups

![🎯](<Base64-Image-Removed>) Auto Stop on Reply

![🎯](<Base64-Image-Removed>) Test Email Before Sending

Complete view


---


## Webhook Guide (DEPRECATED)

**URL:** https://help.smartlead.ai/Webhook-Guide-DEPRECATED-8f10faa000ee4959820cd74c2b8c35f7


[Skip to content](https://help.smartlead.ai/Webhook-Guide-DEPRECATED-8f10faa000ee4959820cd74c2b8c35f7#main)

![🪝 Page icon](<Base64-Image-Removed>)![🪝 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1fa9d.svg)

# Webhook Guide (DEPRECATED)

Please use → [https://helpcenter.smartlead.ai/en/articles/35-webhook-guide](https://helpcenter.smartlead.ai/en/articles/35-webhook-guide)

Automate your outbound by reacting to different events in your campaigns.

Here’s a simple breakdown on how to achieve this:

1) Open your [smartlead dashboard](https://app.smartlead.ai/)

2) Head over to your [settings page](https://app.smartlead.ai/app/settings/profile)

3) On the left panel click on [webhook](https://app.smartlead.ai/app/settings/webhook)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F06edf61b-8b8a-46d6-b6cc-b583759ccccf%2FScreen_Shot_2022-06-29_at_4.47.34_pm.png?table=block&id=2f224c5a-61f4-4cfd-8d14-824ea43c55df&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=770&userId=&cache=v2)

4) Click “Add Webhook”

5) From the popup add your webhook name (this is just for easy maintenance for you)

6) Select the Campaign from which you want to listen to “events” from

7) Select all the events you want attached to the campaign

[Event’s Include:](https://help.smartlead.ai/Event-s-Include-a8959d234e984b63b25bb9f6fed28539?pvs=25)

\- Email sent
\- Email opened
\- Email replied
\- Link clicked
\- Lead unsubscribed
\- Campaign completed
\- Category updated (Interested, Meeting requested, Not interested etc..)

Each event will send a JSON body containing specific data to that event. That information is as such:

EMAIL\_OPENED:

{
stats\_id: <id of the event>
event\_type:"EMAIL\_OPEN"
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_opened: <time email was opened>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
sequence\_number: <the sequence number that triggered this event>
subject: <subject of the message sent>
sent\_message\_body: <body of the message sent>
}

​

EMAIL\_SENT:

{
stats\_id: <id of the event>
event\_type:"EMAIL\_SENT"
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_sent: <time email was sent>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
sequence\_number: <the sequence number that triggered this event>
subject: <subject of the message sent>
sent\_message\_body: <body of the message sent>
message\_id: <unique id of that exact message sent>
}

​

EMAIL\_REPLIED:

{
stats\_id: <id of the event>
event\_type:"EMAIL\_REPLY"
from\_email: <mailbox used>
subject: <subject>
to\_email: <lead email>
to\_name: <lead name>
time\_replied: <time email was replied to>
sent\_message\_body: <body of the message sent>
reply\_body: <copy of the reply from the lead in full copy (html if there is)>
preview\_text: <copy of the latest reply in plain text>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
sequence\_number: <the sequence number that triggered this event>
client\_id: <id of client attached to campaign if it belongs to a client>
}// Threaded Replies{"stats\_id":"48c3ee6c-d639-4ca6-8e4e-0d1e19de1c35","stats\_thread\_id":768605,// stats\_thread\_id to identify it as a thread"from\_email":"m.rameshkumarjain@outlook.com","subject":"Sub 1","sent\_message\_body":"<div>testing push to sub sequence with text.</div>","to\_email":"ramesh@five2one.com.au","to\_name":"Ramesh Kumar","time\_replied":"2023-07-04T16:35:35+00:00","reply\_body":"MESSAGE","message\_id":"<CALsAoD>","preview\_text":"Final thread.","campaign\_name":"Push to SIUUU","campaign\_id":34025,"client\_id":6,"sequence\_number":1,"webhook\_url":"https://webhook.site/81deb413-d7ea-419b-8d25-c2f8a2e0f1f4","event\_type":"EMAIL\_REPLY"}

​

LINK\_CLICKED:

{
stats\_id: <id of the event>
event\_type:"EMAIL\_LINK\_CLICK"
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_clicked: <time link was clicked>
link\_clicked: <which link was clicked>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
sequence\_number: <the sequence number that triggered this event>
subject: <subject of the message sent>
sent\_message\_body: <body of the message sent>
}

​

LEAD\_UNSUBSCRIBED:

{
event\_type:"LEAD\_UNSUBSCRIBED"
lead\_email: <email of lead that unsubscribed>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
}

​

LEAD\_CATEGORY\_UPDATED:

{"event\_type":"LEAD\_CATEGORY\_UPDATED","category":"Interested","lead\_email":"ramesh@five2one.com.au","lead\_data":{"first\_name":"Ramesh","linkedin\_profile":"linkedin.com","custom\_fields":{ first\_line:"Super massive black hole"},"last\_name":"Kumar","phone\_number":"23454212","company\_name":"Smartlead","website":"smartlead.ai","location":"global","company\_url":"smartlead.ai",},"lead\_name":"Ramesh","lead\_category\_id":1,"campaign\_name":"GOauth Testing 1","campaign\_id":750,"from":"vaibhav@usesmartlead.com","to":"andy@fortrasearch.com","history":\[5\],// message\_id, stats\_id added for master inbox reply API"lastReply":{3}}

​

[Full Webhook Reply Response](https://help.smartlead.ai/Full-Webhook-Reply-Response-66e769287b114d93adf6eeec62a6d948?pvs=25)

7) The URL defines the

endpoint

or url to which you want to send the above data to. This could be a custom data point created by a developer, slack webhook for slack notifications, a zapier webhook endpoint


---


## Lead Categories

**URL:** https://help.smartlead.ai/Lead-Categories-da81969e563444c28b9e1c100a561ab8


[Skip to content](https://help.smartlead.ai/Lead-Categories-da81969e563444c28b9e1c100a561ab8#main)

![🎸 Page icon](<Base64-Image-Removed>)![🎸 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f3b8.svg)

# Lead Categories

You may want to react to leads based on their response and use it for your reporting as well as overall management.

You can do that with Smartlead categories.

In the master inbox, on the top right of each conversation you have a dropdown to select the category the conversation belongs to.

You can add additional categories from the Settings section.

You can use “categories” as triggers to your subsequences too, making the entire smartlead experience extremely powerful and automated.

e.g if lead is marked as “Requested info”, auto-add them to the “Send more info” drip sequence.

Default Available Categories for all leads in Smartlead

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F452f105a-cfea-462d-a25f-92f5c9c1f4b7%2FScreen_Shot_2022-08-31_at_11.43.23_am.png?table=block&id=c489a0e6-3fe8-4618-bb4f-4d368ee08d80&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=940&userId=&cache=v2)

Selecting a lead’s category in the master inbox

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F6a997829-8d30-42af-9546-942c4910da57%2FScreen_Shot_2022-08-31_at_11.44.06_am.png?table=block&id=cd08d36d-d2c3-404e-b95e-4a31743484f3&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=940&userId=&cache=v2)


---


## Creating a cold email campaign

**URL:** https://help.smartlead.ai/Creating-a-cold-email-campaign-abfaaa785ecb4254b4ae23ca39d57d2c


[Skip to content](https://help.smartlead.ai/Creating-a-cold-email-campaign-abfaaa785ecb4254b4ae23ca39d57d2c#main)

![💰 Page icon](<Base64-Image-Removed>)![💰 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f4b0.svg)

# Creating a cold email campaign

Full video tutorial here:

SmartLead Demo

[SmartLead Demo](https://www.loom.com/share/057fbfc6cc5143c1a867177f6c1da5ae "SmartLead Demo")

1.02K views

Copy link

[Open video in Loom](https://www.loom.com/share/057fbfc6cc5143c1a867177f6c1da5ae)

0

1.2×

8 min⚡️9 min 22 sec7 min 30 sec6 min 15 sec5 min4 min 24 sec3 min 45 sec3 min

![](https://cdn.loom.com/sessions/thumbnails/057fbfc6cc5143c1a867177f6c1da5ae-1653637947880.jpg)

Your user agent does not support the HTML5 Video element.

[SmartLead Demo](https://www.loom.com/share/057fbfc6cc5143c1a867177f6c1da5ae "SmartLead Demo")

1.02K views

Copy link

[Open video in Loom](https://www.loom.com/share/057fbfc6cc5143c1a867177f6c1da5ae)

0

1.2×

8 min⚡️9 min 22 sec7 min 30 sec6 min 15 sec5 min4 min 24 sec3 min 45 sec3 min

- - ❤️








      heart

      1

  - 👍








    yes

    2

  - 🔥








    fire

    3

  - 👏








    clap

    4

  - 🙌








    yay

    5

  - 👀








    eyes

    6


More reactions

7

✋

## Frequently Used

  - 💯

  - 🎉

  - ✅

  - ❌

  - 👀

  - ✨

  - 🚀

  - ➕

  - 🙏

  - 🔥

  - 😆

  - 🤔

  - 😱

  - 👋

  - 🌈

  - ❤️

  - 👏

  - 🐞


## Smileys & Emotion

## People & Body

## Animals & Nature

## Food & Drink

## Activities

## Travel & Places

## Objects

## Symbols

## Flags

Make frequently used emojis my default

Comment

Comment

C

0 Comments

Step 1:

Navigate to the Email Campaign tab from the left had nav and click on “Add Campaign”

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fa2733662-02d5-4558-b8b0-b111936bc4ff%2FScreen_Shot_2022-06-20_at_7.03.04_pm.png?table=block&id=95356214-3234-45bf-988c-f9a2f1bffe3c&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Step 2:

You’ll be prompted to upload a CSV containing your lead list and their data.

At the same time you can also name your campaign to make it easy for you to identify. I’ve named mine Startup founders Canada, <subniche> <niche> <location>. This helps with management, you soon won’t need to worry about that, with the ability to filter by “tags”

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fec578622-77e8-443f-934f-59d7e1ad89b8%2FScreen_Shot_2022-06-20_at_7.05.40_pm.png?table=block&id=ae0e0487-a867-4ad2-b1e1-a8bdefb31817&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Step 3:

Map each column in your CSV to the relevant columns from the drop down.

In some cases you’ll want to add additional fields than the ones available in the dropdown e.g “Custom First Line”, this can be added by mapping that field to the

Custom field

option in the dropdown.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F4cff3450-076a-42a4-a643-3137d9c29f26%2FScreen_Shot_2022-06-20_at_7.10.18_pm.png?table=block&id=ad292d7c-9432-41da-9442-9988b3e60123&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Step 4:

On the Mail sequence stage, you can start writing your eye grabbing subject line.

Starting with the subject line, you can inject your variables into it by simply typing

{{

and using the dropdown options made available

Step 5:

Plop in your juicy high converting copy next, using the editor, that lets you get the full power of a rich text editor.

You have access to all your (custom) variables in the main text editor as well.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Faa5ad5e6-0087-4f4c-8f55-9f75791b2871%2FScreen_Shot_2022-06-20_at_7.34.26_pm.png?table=block&id=e0fcb011-013c-473d-9841-3aa2a4b9a1c3&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Make use of the readability engine which guides you to improve your copy writing and readability score. Everyone’s busy, so you want to make sure your emails are short, easy to read and have a powerful offer.

Step 6:

You can add a follow up step in your cold email sequence by clicking on the + icon and defining a delay between sending the second email from the first email.

With Smartlead, you can add as many follow up sequences as you’d like, however industry practice is to limit it to 4-5 emails.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Ff2716d30-cd63-495a-bc49-f3a2bb80e3a7%2FScreen_Shot_2022-06-20_at_7.45.34_pm.png?table=block&id=1d70d917-fa4b-47ea-a1b3-7ac7adfc8ad9&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

If you’d like to remove a step in the sequence, click on the bin icon.

PS: If you do not add a subject line to a follow up email, it will show up as a reply to the same email thread as the previous email. If you do add a subject line, it will be sent as a new email.

Email editorial tips:

Links:

You can easily add a link to your email copy, by highlighting a piece of text, and clicking on the “Link” button at the top of the editor, you’ll be shown a popup, within which you can add the url of the link.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F18dd3b06-5efc-48c7-9c44-ab450117b57d%2FScreen_Shot_2022-06-20_at_7.48.25_pm.png?table=block&id=1b88f5a0-adc3-4d11-9c96-ccef8bbc1325&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Unsubscribe link:

If it’s part of your email flavour, you can add an unsubscribe link with a custom unsubscribe text message which will show up at the end of your emails.

Click on the settings at the top right of the screen, you’ll se a popup, scroll down and select the unsubscribe link option

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F39c3cdf3-c96a-455f-b662-96c973d8a879%2FScreen_Shot_2022-06-20_at_7.52.40_pm.png?table=block&id=48626e85-57fb-4e68-8959-c1a376677b19&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Step 7:

Set up a schedule to instruct Smartlead’s smart sending algorithm on when to send emails to your leads.

You can decide the time zone, the time period during the day, as well as the time gap between sending emails.

Smartlead uses reactive sending algorithms that emulate “human” sending patterns to boost deliverability.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F3b2bfbbf-2b00-42bb-96bd-f395a11075fb%2FScreen_Shot_2022-06-20_at_8.07.55_pm.png?table=block&id=93b57e98-dffa-4750-b6b4-fdec8b73464c&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Step 8:

Review your email copy to ensure it matches your exact needs. The variable data will be injected at this point, so this is exactly how your lead will read the email too.

If you’re not happy with one person’s copy, you can individually edit just that person’s copy, click save. This won’t effect the copy of all your other leads but just that one person.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Faf26cf76-707f-47e9-acd7-93b24bd4096c%2FScreen_Shot_2022-06-20_at_8.11.04_pm.png?table=block&id=8d983307-6182-42c1-8db8-bef5dbe9a04d&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Take advantage of the Mobile preview to see how your leads will view your email. 68% of emails are opened on mobile view, this is a good opportunity to reformat any “walls of text”.

Also use this chance to ensure your subject line copy is visible

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F69866a27-e828-47f0-b521-b637c291001b%2FScreen_Shot_2022-06-20_at_8.15.06_pm.png?table=block&id=99eb65f5-94bc-45e5-b074-0eb2d10bd492&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

If you’ve added a sender email account, you’re done :). Click on start campaign, select all the sender email accounts you want Smartlead to auto-rotate through and you’re off to the races ![🏎](<Base64-Image-Removed>).

Get that wifi money ![💸](<Base64-Image-Removed>)​

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fc59130c2-d358-4062-ba08-42dff0a357ad%2FScreen_Shot_2022-06-20_at_8.25.37_pm.png?table=block&id=be924174-4e60-4b7b-944c-72e459903e13&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

If you don’t have an email account added, click on the button to “Add an Account”, and follow these simple steps to add your email account:

![👉](<Base64-Image-Removed>)[Google](https://help.smartlead.ai/f880fd88217741b983e26846d322d6c3)

![👉](<Base64-Image-Removed>)[Zoho](https://help.smartlead.ai/7e1e28c292a74631bc106ee36d0f5731)

![👉](<Base64-Image-Removed>)[Outlook/Microsoft 365](https://help.smartlead.ai/c9fd51c4fe7a470d8b4efaa213e74eae)

![👉](<Base64-Image-Removed>)[SMTP](https://help.smartlead.ai/7e1e28c292a74631bc106ee36d0f5731)


---


##  Multi Channel Outreach

**URL:** https://help.smartlead.ai/Multi-Channel-Outreach-f4ceeabce0054a4ba754c3b16f52e85d


[Skip to content](https://help.smartlead.ai/Multi-Channel-Outreach-f4ceeabce0054a4ba754c3b16f52e85d#main)

# ![🎯](<Base64-Image-Removed>) Multi Channel Outreach

Date

January 1, 2023 → February 25, 2023

Assign

Empty

Status

Empty


---


## What is custom domain tracking?

**URL:** https://help.smartlead.ai/What-is-custom-domain-tracking-38a5fbbd8e6141f488e7a0186fa29f86


[Skip to content](https://help.smartlead.ai/What-is-custom-domain-tracking-38a5fbbd8e6141f488e7a0186fa29f86#main)

![👣 Page icon](<Base64-Image-Removed>)![👣 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f463.svg)

# What is custom domain tracking?

Custom domain tracking setup:

Custom Domain Tracking SmartLead

[Custom Domain Tracking SmartLead](https://www.loom.com/share/ecc9e1e3d5d24a1689449d8051db1437 "Custom Domain Tracking SmartLead")

8.3K views

Copy link

[Open video in Loom](https://www.loom.com/share/ecc9e1e3d5d24a1689449d8051db1437)

0

1.2×

1 min 13 sec⚡️1 min 31 sec1 min 13 sec1 min48 sec42 sec36 sec29 sec

![](https://cdn.loom.com/sessions/thumbnails/ecc9e1e3d5d24a1689449d8051db1437-1655339784997.jpg)

Your user agent does not support the HTML5 Video element.

[Custom Domain Tracking SmartLead](https://www.loom.com/share/ecc9e1e3d5d24a1689449d8051db1437 "Custom Domain Tracking SmartLead")

8.3K views

Copy link

[Open video in Loom](https://www.loom.com/share/ecc9e1e3d5d24a1689449d8051db1437)

0

1.2×

1 min 13 sec⚡️1 min 31 sec1 min 13 sec1 min48 sec42 sec36 sec29 sec

- - ❤️








      heart

      1

  - 👍








    yes

    2

  - 🔥








    fire

    3

  - 👏








    clap

    4

  - 🙌








    yay

    5

  - 👀








    eyes

    6


More reactions

7

✋

## Frequently Used

  - 💯

  - 🎉

  - ✅

  - ❌

  - 👀

  - ✨

  - 🚀

  - ➕

  - 🙏

  - 🔥

  - 😆

  - 🤔

  - 😱

  - 👋

  - 🌈

  - ❤️

  - 👏

  - 🐞


## Smileys & Emotion

## People & Body

## Animals & Nature

## Food & Drink

## Activities

## Travel & Places

## Objects

## Symbols

## Flags

Make frequently used emojis my default

Comment

Comment

C

0 Comments

Tracking clicks and open rates depends on a small snippet of html being injected into your email body. This is industry standard. Whilst it makes for good analytics sometimes people may see drops in their campaigns deliverability.

This is due to the same “tracking” domain being used across 1000s of campaigns setup by all the users of the cold emailing software. ESPs (email service providers) are smart to understand that there’s millions of emails being opened and they’re all sending “requests” to the same “tracking url”. This may\* cause a slight drop in your deliverability.

So what’s the fix? Simple.

You trick the ESP by “masking” the tracking url with your own.

### Step 1:

Add a new email account / open an existing email account within smartlead

Scroll down to

Custom tracking domain

### Step 2:

Open your domain management tool e.g Godaddy, Namecheap, Crazydomains etc

Head over to the DNS management section

In your Host Records section add in a CNAME with the following

Type: CNAME Record

Host:

emailtracking

Value:

open.sleadtrack.com

TTL:

Automatic

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F8a8c8522-47bf-4e4a-9737-ba716d623cc7%2FScreen_Shot_2022-06-16_at_11.26.36_am.png?table=block&id=dbd2ea0c-75db-48dd-ae6f-28c1c1c4e9d8&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Once this is done, wait for 30 mins to 24 hour to be bubbled to your account.

Now head over to your app and paste the full url into the text field like below in this format

http://{host}.{yourdomain}

In my case my domain is [getsmartwriter.co](http://getsmartwriter.co/) and my host is emailtracking

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fbb81818b-eb7d-43c5-8a4f-47009d7fe738%2FScreen_Shot_2022-06-16_at_11.22.48_am.png?table=block&id=b7b3c59f-89b2-49c5-a97e-59f35b6be9e5&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

#### Verify Your CNAME Tracking

If you’ve done thing’s right. Click on the “Verify CNAME” button. It’ll take you to a [nslookup.io](http://nslookup.io/) link.

If underneath the “Canonical name” it says “open.sleadtrack.com”, then you did it right.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F85070967-020b-482a-98f8-0cd242402e8f%2FScreen_Shot_2022-07-22_at_3.29.55_pm.png?table=block&id=79bca0ce-6b3c-4813-8681-d9ca788ebd90&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### Domain Tracking Tips

#### Combined tracking / Account level Tracking

If you have an aged domain, or a domain with good reputation, you can use that single domain for tracking, instead of setting up a custom tracking per email domain.

For e.g, if you have a well reputed / old domain named

smartlead.com

, you can do the CNAME process (listed above) to that domain and use [emailtracking.smartlead.com](http://emailtracking.smartlead.com/) across all the mailboxes in your Smartlead account.

So vaibhav@getsmartlead.com, v@usesmartlead.com etc will all have tracking point to

emailtracking.smartlead.com

This works well if you’re working with clients too, where you can condense tracking to a single domain.

#### Individual Tracking

If you’re running experiments, starting off fresh or want to build up the authority across multiple domains you can set up individual tracking per domain. Unlike the above configuration where a common tracking is shared across all your mailboxes, in this case you can have it siloed per account.

Using the above example:

For v@ [usesmartlead.com](http://usesmartlead.com/) the usesmartlead.com domain will need to have a CNAME configuration for

emailtracking

pointing to

open.sleadtrack.com

For vaibhav@getsmartlead.com the getsmartlead.com domain will need to have a CNAME configuration for

emailtracking

pointing to

open.sleadtrack.com

So on and so forth


---


## Connect Zoho Mail

**URL:** https://help.smartlead.ai/Connect-Zoho-Mail-7e1e28c292a74631bc106ee36d0f5731


[Skip to content](https://help.smartlead.ai/Connect-Zoho-Mail-7e1e28c292a74631bc106ee36d0f5731#main)

# Connect Zoho Mail

[Buying and Setting Up A Zoho Account](https://help.smartlead.ai/Buying-and-Setting-Up-A-Zoho-Account-00146eec31af43988538284c921208bc?pvs=25)

You can also follow [Zoho’s own documentation](https://www.zoho.com/mail/help/imap-access.html) for setup

### 1 - Setup Your IMAP

Open Zoho on your desktop and login to your [Zoho Mail](http://www.zoho.com/mail/login.html)

Go to Settings

1\. Navigate to [Mail Accounts](https://mail.zoho.com.au/zm/#settings/all/mailaccounts) and click the respective email address from the left listing.

Under the IMAP  section, check the IMAP Access  box.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F90b004f5-13d0-488c-ab3f-278e5152a291%2Fimapaccess12.jpeg?table=block&id=264a6166-66d4-4730-b1d3-d54dfc5291a2&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=1980&userId=&cache=v2)

> Note your SMTP url here

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fd836a834-f947-457d-a035-ba3ea2f4612c%2FScreen_Shot_2022-07-28_at_11.01.35_pm.png?table=block&id=900faed4-ae06-48f2-89e9-cac13bfe447e&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=770&userId=&cache=v2)

> Note your IMAP url here

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F22983124-e531-4d9e-bf92-13510e4e8c38%2FScreen_Shot_2022-07-28_at_11.02.48_pm.png?table=block&id=641c0ef6-704b-43e0-86de-67d936ec12be&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=580&userId=&cache=v2)

### 2 - Final Step

Go to [app.smartlead.ai](http://app.smartlead.ai/) and navigate to the [Email Accounts](https://app.smartlead.ai/app/email-accounts) tab

Click on Add Account

Type in your email address & password with the other pieces of information shown in the image below & voila!

SMTP Host:

[smtp.zoho.com.au](http://smtp.zoho.com.au/) (this changes based on the location you’re at, copy it from your “POP3 Out” SMTP setting as shown above)

SMTP Port: 465

AND

SSL: True

Or

SMTP Port: 587

AND

TLS: True

IMAP Host:

[imap.zoho.com.au](http://imap.zoho.com.au/) (this changes based on the location you’re at, copy it from your “IMAP In” setting as shown above)

IMAP Port: 993

SSL: True

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Ffc90da9f-094d-43a6-a0aa-f09aaa65f084%2FScreen_Shot_2022-05-25_at_2.01.29_pm.png?table=block&id=bab91e2d-ce0c-4ff2-84c4-07590fa41a30&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Test your connection by clicking on the Test Connection Button

You would have received a test mail on the email account you signed up to Smartlead on

Once confirmed you’ll see a success message

And voila!

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F490d422a-811a-4219-b976-b0062acdd340%2FScreen_Shot_2022-05-25_at_2.29.49_pm.png?table=block&id=2820c4e9-006a-489c-bf8e-ddc59d7fc734&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Feel free to add your signature which will be added to all your emails automatically and click Save


---


## Connect Microsoft Office 365 / Outlook

**URL:** https://help.smartlead.ai/Connect-Microsoft-Office-365-Outlook-c9fd51c4fe7a470d8b4efaa213e74eae


[Skip to content](https://help.smartlead.ai/Connect-Microsoft-Office-365-Outlook-c9fd51c4fe7a470d8b4efaa213e74eae#main)

# Connect Microsoft Office 365 / Outlook

### 1 - Step 1

Go to [app.smartlead.ai](http://app.smartlead.ai/) and navigate to the [Email Accounts](https://app.smartlead.ai/app/email-accounts) tab

Click on Add Account

Type in your email account & password with the other pieces of information in the image below & voila!

SMTP Host: smtp.office365.com

SMTP Port: 587

TLS: True

IMAP Host: outlook.office365.com

IMAP Port: 993

SSL: True

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fda0dc3a9-0448-482a-9935-6c6b714fd4b8%2FScreen_Shot_2022-05-25_at_2.22.03_pm.png?table=block&id=45437225-0c1c-40d1-a6f1-037b5be3b419&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Test your connection by clicking on the Test Connection Button

You would have received a test mail on the email account you signed up to Smartlead on

Once confirmed you’ll see a success message

And voila!

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fd06dd292-7034-4298-beaa-f3b7bf477554%2FScreen_Shot_2022-05-25_at_2.30.50_pm.png?table=block&id=7cce2c5b-5f12-4673-9bf2-909c2b73e8c1&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Feel free to add your signature which will be added to all your emails automatically and click Save

### 2 - Click Save

In a situation you get an error message or the connection fails, you might need to enable 2 step verification for Outlook

Head to your [outlook account](https://outlook.live.com/mail/0/inbox) on your desktop

Click on [My Profile](https://accounts.microsoft.com/profile) from the dropdown option on the top right (click on you avatar)

In the top menu select Security Tab and then Advanced Security

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fe1e667aa-a4e8-4c21-88c3-8eeeb9c65868%2FScreen_Shot_2022-05-25_at_2.24.24_pm.png?table=block&id=a98a0551-ade2-4c97-90c1-7335ef670db1&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Turn on 2 Step Verification

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F2c21e606-0786-4749-af01-b4ee0be65046%2FScreen_Shot_2022-05-25_at_2.25.02_pm.png?table=block&id=45123c6b-4f6d-439a-8c90-d259b543d9db&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Follow the instructions accordingly

One done, create an App Password

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F11ff396a-1883-4146-8836-92ac0507734e%2FScreen_Shot_2022-05-25_at_2.26.14_pm.png?table=block&id=f3bf06d8-bb9a-432e-8971-bd7ef21a8dd5&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Copy the given password and use that in the password section in the email accounts section of Smartlead (instead of your normal password used for logging in to Outlook)


---


## Bulk Add Email Account

**URL:** https://help.smartlead.ai/Bulk-Add-Email-Account-af48c91fb7584dc398c968831091b389


[Skip to content](https://help.smartlead.ai/Bulk-Add-Email-Account-af48c91fb7584dc398c968831091b389#main)

![🚛 Page icon](<Base64-Image-Removed>)![🚛 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f69b.svg)

# Bulk Add Email Account

We get it, adding email accounts 1 by 1 can be a pain, especially when you’re coming from another service.

The goal of smartlead is to help you scale your outreach using unlimited email accounts at no extra cost, so it’s only fair that the experience of adding email accounts should be easy.

And so we built email account bulk import, here’s how you can use it to cut down 1 hour to 2 minutes.

1) Open your [email accounts](https://app.smartlead.ai/app/email-accounts)

2) Click on “Add Account(s)”

3) Click on the “here” to review the sample CSV which needs to be followed for the upload to work.

Here’s the [link](https://docs.google.com/spreadsheets/d/1j-y2m5IemxARkZqI0cbgKOjtqWh3D3lNnLawfDnndgc) again.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F57f7fb0c-79d6-42fb-8587-605a4ba4d453%2FScreen_Shot_2022-08-19_at_12.55.10_am.png?table=block&id=4da6603b-69a5-499d-8772-093e43116757&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

4)Once you upload the CSV you’ll get a preview of the CSV and immediate feedback on any invalid details you might have put in

Setting the warmup number too high

Missing password etc etc

5)If you have errors you can choose to skip those and just upload the valid ones or reupload

6) Voila, you can see the live status of your email accounts being added

7) Once processed, you’ll get an email with a link to your email accounts upload status, if opened will look like this

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fbc39c210-b94d-443c-bf8a-79ab0c67bf4a%2FScreen_Shot_2022-08-19_at_12.58.39_am.png?table=block&id=2492b87c-c290-456f-8da0-d4fe32d6eed1&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

You can see the success state, if errors you’ll see why there’s an error.


---


## Scheduled reminders from Master Inbox

**URL:** https://help.smartlead.ai/Scheduled-reminders-from-Master-Inbox-861c9ecab4ed4eff9c34a1a161017489


[Skip to content](https://help.smartlead.ai/Scheduled-reminders-from-Master-Inbox-861c9ecab4ed4eff9c34a1a161017489#main)

![⏰ Page icon](<Base64-Image-Removed>)![⏰ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/23f0.svg)

# Scheduled reminders from Master Inbox

Date

March 7, 2023

Assign

Empty

Status

Empty


---


## Connect Gmail With SMTP

**URL:** https://help.smartlead.ai/Connect-Gmail-With-SMTP-f880fd88217741b983e26846d322d6c3


[Skip to content](https://help.smartlead.ai/Connect-Gmail-With-SMTP-f880fd88217741b983e26846d322d6c3#main)

# Connect Gmail With SMTP

### 1 - Setup Your IMAP

Open Gmail on your desktop and head over to the [settings tab](https://mail.google.com/mail/u/0/#settings/general)

Select the Forwarding and POP/IMAP tab on the top

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fc832f66a-ea28-4d73-b08e-eb0cadde5299%2FScreen_Shot_2022-05-25_at_12.58.36_am.png?table=block&id=9ae225e7-f9c7-4757-9ba0-08bea0966e2d&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Select Enable IMAP and click on Save Changes

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fd6dc01d1-9493-4609-ad70-ab1c6631effa%2FScreen_Shot_2022-05-25_at_12.59.29_am.png?table=block&id=3a069e85-fce4-4704-832e-efaea174f991&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### 2- Enabling 2 Factor Authentication

Head over to your [Google Account](https://myaccount.google.com/)

Navigate to the [Security tab](https://myaccount.google.com/security) on the left side

Select Enable 2 Step Verification if it

not

Enabled. In a situation it is, skip the rest of this step and go to the next

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F76b9a4d8-dfde-4274-8845-7a8cfef12352%2FScreen_Shot_2022-05-25_at_1.28.09_am.png?table=block&id=a992bffb-25e4-4e16-a07b-cc6798e6b660&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Click on get started

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F1c497436-2ea4-4046-8020-1ef73a83f92f%2FScreen_Shot_2022-05-25_at_1.28.53_am.png?table=block&id=727536a2-4a43-4d22-8383-6d6fabbb15d2&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

You’ll be prompted to add your password again, go ahead and do so

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F453a464f-2125-45d2-b286-db96f4333f33%2FScreen_Shot_2022-05-25_at_1.29.21_am.png?table=block&id=3573631f-b928-4636-9e29-06b228da9486&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Verify the device to which you’d like to get the verification code

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F93ce5f0e-d682-4345-b8c0-e7e80767ad71%2FScreen_Shot_2022-05-25_at_1.30.29_am.png?table=block&id=39b031aa-2087-4422-998f-4fee9caccdae&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Type in your phone number

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F6a2f22eb-5804-439f-bd4e-9e0fff17ad8d%2FScreen_Shot_2022-05-25_at_1.31.10_am.png?table=block&id=e9178af5-87b3-4c27-b03d-d5b93d3c3bfe&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Enter the code you would have just received

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F4e1042b8-c0c1-4aae-aea9-00bba8da16fe%2FScreen_Shot_2022-05-25_at_1.31.59_am.png?table=block&id=41f5da48-660b-43a9-8244-70bb864c6445&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Verify the details and click on Turn on

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F8539b31a-aeb1-4a4b-9e64-509ad8e4ba64%2FScreen_Shot_2022-05-25_at_1.32.45_am.png?table=block&id=c45981ad-621f-4f6c-8b50-fa493b3aaeb5&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

If you head back to the [Security Tab](https://myaccount.google.com/security), you should now see a tick mark next to 2-Step Verification

### 3 - Creating an App Password

Head over to your [Google Account](https://myaccount.google.com/)

Navigate to the [Security tab](https://myaccount.google.com/security) on the left side

Select on App Passwords

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fdd8443a4-3e3b-47d1-8e64-e758bce137d8%2FScreen_Shot_2022-05-25_at_1.15.20_am.png?table=block&id=60284768-567f-4022-a4fa-aa22c948da22&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

You may be prompted to re-enter your gmail account password again, if so, please go ahead and type it in

In the dropdown select the Mail option, and for the device dropdown, select Other (custom name)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fd0afff60-1400-4b7a-a070-18a130951cfb%2FScreen_Shot_2022-05-25_at_1.17.00_am.png?table=block&id=03f95299-4e76-45e9-be0c-9b4f1b6b5ad7&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Name it something relevant to Smartlead to make it easy to identify down the road, then click Generate

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F27767e78-13a8-4832-868e-078cf2313fd5%2FScreen_Shot_2022-05-25_at_1.18.05_am.png?table=block&id=4d8a8e31-cac3-410e-84cc-368139baa830&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

You’ll have a password generated, which you need to copy and keep safely

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F61691b10-b50e-4a1c-b74e-5d222253706d%2FScreen_Shot_2022-05-25_at_1.18.58_am.png?table=block&id=28fb6a9c-6b50-4d19-bb9e-ba7a267b6a00&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### 4 - Final Step

Go to [app.smartlead.ai](http://app.smartlead.ai/) and navigate to the [Email Accounts](https://app.smartlead.ai/app/email-accounts) tab

Click on Add Account

Type in your email account & password with the other pieces of information in the image below & voila!

SMTP Host: smtp.gmail.com

SMTP Port: 465

SSL: True

IMAP Host: imap.gmail.com

IMAP Port: 993

SSL: True

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F73b3997b-2740-42b1-8102-d3f281fe303e%2FScreen_Shot_2022-05-25_at_1.46.26_am.png?table=block&id=3aa1016d-616a-4bf2-8c71-86563d7fe625&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Test your connection by clicking on the Test Connection Button

You would have received a test mail on the email account you signed up to Smartlead on

Once confirmed you’ll see a success message

And voila!

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fad7f8016-2d71-4504-89d8-bab25c5fdcad%2FScreen_Shot_2022-05-25_at_2.37.29_pm.png?table=block&id=eb745c94-123d-4e43-a212-f953544db4b1&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Feel free to add your signature which will be added to all your emails automatically and click Save


---


## How do you use Spintax?

**URL:** https://help.smartlead.ai/How-do-you-use-Spintax-d305363b8e564bf7bcba7662a2d6290d


[Skip to content](https://help.smartlead.ai/How-do-you-use-Spintax-d305363b8e564bf7bcba7662a2d6290d#main)

![🌀 Page icon](<Base64-Image-Removed>)![🌀 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f300.svg)

# How do you use Spintax?

Why use Spintax?

The goal is to improve your deliverability and avoid spam pockets. Sending “different” versions of the same CTA or text, prompts email service providers into thinking you’re sending a different email to different people vs the same email to 1000 people, in effect not treating it as a “mass” cold email.

The game of cold emailing is to “trick” ESPs (email service providers) into thinking you’re sending emails with genuine intention and looking to engage in conversation. So spintax allows for that as even though a percentage of the email will be the same, having microcopy differences improves the deliverability of your email with 0/minimal extra effort.

The other advantage is you get to see which copywriting format is converting the best for your audience for free.

### Step 1:

Open your email editor/composer.

This can be done by editing an existing campaign

Creating a new campaign

### Step 2:

In the text editor, place your Spintax text in this format:

{Let's jump on a call \| Are you free tomorrow? \| Keen for a demo ?}

​


---


## Complete Roadmap

**URL:** https://help.smartlead.ai/b0f93a0712984e0ba5471ed0b23cdf02?v=4435ebd00d194454a6ad3dcb67a1b87f


[Skip to content](https://help.smartlead.ai/b0f93a0712984e0ba5471ed0b23cdf02?v=4435ebd00d194454a6ad3dcb67a1b87f#main)

![🛣️ Page icon](<Base64-Image-Removed>)![🛣️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f6e3-fe0f.svg)

# Complete Roadmap

Timeline view

![👀](<Base64-Image-Removed>) Test Email Before Sending

![📥](<Base64-Image-Removed>) Email Warmup

![🅰️](<Base64-Image-Removed>)/ ![🅱️](<Base64-Image-Removed>) A/B Testing

![🏝](<Base64-Image-Removed>) Agency Views

![🎯](<Base64-Image-Removed>) Multi Channel Outreach

![🪝](<Base64-Image-Removed>) Webhooks

![🤖](<Base64-Image-Removed>) AI Email Writer + Spam checker

![💻](<Base64-Image-Removed>) Dedicated IP access

![💫](<Base64-Image-Removed>) Replying from Master Inbox

![🏜️](<Base64-Image-Removed>)

Whitelabel Clients Given Credits

![🪐](<Base64-Image-Removed>)

Global lead list management

![🏏](<Base64-Image-Removed>)

Native CRM Integrations

![🌊](<Base64-Image-Removed>)

Liquid Syntax

![🎞️](<Base64-Image-Removed>)

Email Templates

![🎍](<Base64-Image-Removed>)

Account Wide Global Analytics

![💺](<Base64-Image-Removed>)

Multiple Seats

![](https://help.smartlead.ai/icons/archery_gray.svg?mode=light)

Full Create Campaign API Access

![🧙](<Base64-Image-Removed>)

Whitelabelling Full Access

![🔬](<Base64-Image-Removed>)

Microsoft oAuth

![💰](<Base64-Image-Removed>)

Subsequences

![✏️](<Base64-Image-Removed>)

Signature As Handle Bar

![⚡](<Base64-Image-Removed>)

Gmail oAuth

![🤖](<Base64-Image-Removed>)

API Access To Everything

![📈](<Base64-Image-Removed>)

CSV Reports

![🌅](<Base64-Image-Removed>)

Beta Agency View

![✋🏾](<Base64-Image-Removed>)

Global Block List

![💼](<Base64-Image-Removed>)

Custom CRM

![🎞️](<Base64-Image-Removed>)

Images In HTML

![🎿](<Base64-Image-Removed>)

CC In Replies from Master Inbox

![⏰](<Base64-Image-Removed>)

Scheduled reminders from Master Inbox

![🖼️](<Base64-Image-Removed>)

Image Personalisation

October

November

December

January

February

March

April

May

June

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

11

January 2026

Month

Today

Name

![👀](<Base64-Image-Removed>) Test Email Before Sending

![📥](<Base64-Image-Removed>) Email Warmup

![🅰️](<Base64-Image-Removed>)/ ![🅱️](<Base64-Image-Removed>) A/B Testing

![🏝](<Base64-Image-Removed>) Agency Views

![🎯](<Base64-Image-Removed>) Multi Channel Outreach

![🪝](<Base64-Image-Removed>) Webhooks

![🤖](<Base64-Image-Removed>) AI Email Writer + Spam checker

![💻](<Base64-Image-Removed>) Dedicated IP access

![💫](<Base64-Image-Removed>) Replying from Master Inbox

![🤫](<Base64-Image-Removed>)

Chrome Extension

![👀](<Base64-Image-Removed>)

Video Personalisation At Scale

![🛶](<Base64-Image-Removed>)

Conditional Follow up Messages

![🌦️](<Base64-Image-Removed>)

Calendar Freeze Time

![🏜️](<Base64-Image-Removed>)

Whitelabel Clients Given Credits

![🪐](<Base64-Image-Removed>)

Global lead list management

![🏏](<Base64-Image-Removed>)

Native CRM Integrations

![🌊](<Base64-Image-Removed>)

Liquid Syntax

![🎞️](<Base64-Image-Removed>)

Email Templates

![🎍](<Base64-Image-Removed>)

Account Wide Global Analytics

![💺](<Base64-Image-Removed>)

Multiple Seats

![](https://help.smartlead.ai/icons/archery_gray.svg?mode=light)

Full Create Campaign API Access

![🧙](<Base64-Image-Removed>)

Whitelabelling Full Access

![🔬](<Base64-Image-Removed>)

Microsoft oAuth

![💰](<Base64-Image-Removed>)

Subsequences

![✏️](<Base64-Image-Removed>)

Signature As Handle Bar

![⚡](<Base64-Image-Removed>)

Gmail oAuth

![🤖](<Base64-Image-Removed>)

API Access To Everything

![📈](<Base64-Image-Removed>)

CSV Reports

![🌅](<Base64-Image-Removed>)

Beta Agency View

![✋🏾](<Base64-Image-Removed>)

Global Block List

![💼](<Base64-Image-Removed>)

Custom CRM

![🎞️](<Base64-Image-Removed>)

Images In HTML

![🎿](<Base64-Image-Removed>)

CC In Replies from Master Inbox

![⏰](<Base64-Image-Removed>)

Scheduled reminders from Master Inbox

![🖼️](<Base64-Image-Removed>)

Image Personalisation

Timeline view


---


## Account Wide Global Analytics

**URL:** https://help.smartlead.ai/Account-Wide-Global-Analytics-2ba01050d7574e17b3a34e2df0cc81e4


[Skip to content](https://help.smartlead.ai/Account-Wide-Global-Analytics-2ba01050d7574e17b3a34e2df0cc81e4#main)

![🎍 Page icon](<Base64-Image-Removed>)![🎍 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f38d.svg)

# Account Wide Global Analytics

Date

March 18, 2023 → March 21, 2023

Assign

Empty

Status

Empty


---


##  Email Warmup

**URL:** https://help.smartlead.ai/Email-Warmup-0c6e53ac1c284aa7b425987776da9b88


[Skip to content](https://help.smartlead.ai/Email-Warmup-0c6e53ac1c284aa7b425987776da9b88#main)

# ![📥](<Base64-Image-Removed>) Email Warmup

Date

June 13, 2022

Assign

Empty

Status

Completed


---


## Global Block List

**URL:** https://help.smartlead.ai/Global-Block-List-ad2b323a400e46b5a0aad98fcb5d18dd


[Skip to content](https://help.smartlead.ai/Global-Block-List-ad2b323a400e46b5a0aad98fcb5d18dd#main)

![🚫 Page icon](<Base64-Image-Removed>)![🚫 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f6ab.svg)

# Global Block List

There can be situations where you have a list of leads or domains which permanently bounce or leads who’ve asked your company to stop contacting them permanenlty

For such situations you can upload a global block list as a CSV containing domains/emails or manually enter them in the [settings section](https://app.smartlead.ai/app/settings/global-block-list) of your app

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F1a71407c-6678-448c-b661-d348b55fecb6%2FScreen_Shot_2022-07-29_at_12.37.54_am.png?table=block&id=f80b511b-ff02-4b77-8c14-4791011295ee&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Import a CSV containing a column of CSVs OR domains, and map the that column mentioned.

This will ensure any campaign that contains emails in the CSV or emails from domains in the CSV are deleted.

In addition, whenever you upload a new list for any campaign, hence on end, will be thoroughly checked to find any “blocked” domains/emails and will be automatically removed for you to prevent you from reaching out to them and hurting your domain reputation


---


## CSV Reports

**URL:** https://help.smartlead.ai/CSV-Reports-80f705c6caed4a31b3089af8fb796286


[Skip to content](https://help.smartlead.ai/CSV-Reports-80f705c6caed4a31b3089af8fb796286#main)

![📈 Page icon](<Base64-Image-Removed>)![📈 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f4c8.svg)

# CSV Reports

Date

July 6, 2022

Assign

Empty

Status

Completed


---


## Images In HTML

**URL:** https://help.smartlead.ai/Images-In-HTML-be8fe496d06547909804bb2459a56783


[Skip to content](https://help.smartlead.ai/Images-In-HTML-be8fe496d06547909804bb2459a56783#main)

![🎞️ Page icon](<Base64-Image-Removed>)![🎞️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f39e-fe0f.svg)

# Images In HTML

Date

July 11, 2022 → July 14, 2022

Assign

Empty

Status

Completed


---


## Whitelabelling Full Access

**URL:** https://help.smartlead.ai/Whitelabelling-Full-Access-754f503b97094960b5c3ed863d49a8cf


[Skip to content](https://help.smartlead.ai/Whitelabelling-Full-Access-754f503b97094960b5c3ed863d49a8cf#main)

![🧙 Page icon](<Base64-Image-Removed>)![🧙 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f9d9.svg)

# Whitelabelling Full Access

Date

November 1, 2022 → November 3, 2022

Assign

Empty

Status

Completed


---


## Signature As Handle Bar

**URL:** https://help.smartlead.ai/Signature-As-Handle-Bar-2c9536c012044cf3bc3aea78997b34b1


[Skip to content](https://help.smartlead.ai/Signature-As-Handle-Bar-2c9536c012044cf3bc3aea78997b34b1#main)

![✏️ Page icon](<Base64-Image-Removed>)![✏️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/270f-fe0f.svg)

# Signature As Handle Bar

Date

July 25, 2022 → July 26, 2022

Assign

Empty

Status

Completed

Allow users to add {{user\_signature}} within the body of the email.

This merge tag will be replaced with the signature associated with the email account


---


##  AI Email Writer + Spam checker

**URL:** https://help.smartlead.ai/AI-Email-Writer-Spam-checker-4c3a2dc08abb4e8daefc430cdb720783?pvs=25


[Skip to content](https://help.smartlead.ai/AI-Email-Writer-Spam-checker-4c3a2dc08abb4e8daefc430cdb720783?pvs=25#main)

# ![🤖](<Base64-Image-Removed>) AI Email Writer + Spam checker

Date

June 15, 2022

Assign

Empty

Status

Completed


---


##  Replying from Master Inbox

**URL:** https://help.smartlead.ai/Replying-from-Master-Inbox-2489ba8fb8864f3b9486774fc8e7d65b


[Skip to content](https://help.smartlead.ai/Replying-from-Master-Inbox-2489ba8fb8864f3b9486774fc8e7d65b#main)

# ![💫](<Base64-Image-Removed>) Replying from Master Inbox

Date

June 27, 2022 → July 1, 2022

Assign

Empty

Status

Completed


---


## CC In Replies from Master Inbox

**URL:** https://help.smartlead.ai/CC-In-Replies-from-Master-Inbox-44ca523c9ae84025a8fa711bd18c6d81


[Skip to content](https://help.smartlead.ai/CC-In-Replies-from-Master-Inbox-44ca523c9ae84025a8fa711bd18c6d81#main)

![🎿 Page icon](<Base64-Image-Removed>)![🎿 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f3bf.svg)

# CC In Replies from Master Inbox

Date

July 4, 2022

Assign

Empty

Status

Completed


---


## What is custom domain tracking?

**URL:** https://help.smartlead.ai/What-is-custom-domain-tracking-38a5fbbd8e6141f488e7a0186fa29f86?pvs=25


[Skip to content](https://help.smartlead.ai/What-is-custom-domain-tracking-38a5fbbd8e6141f488e7a0186fa29f86?pvs=25#main)

![👣 Page icon](<Base64-Image-Removed>)![👣 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f463.svg)

# What is custom domain tracking?

Custom domain tracking setup:

Custom Domain Tracking SmartLead

Tracking clicks and open rates depends on a small snippet of html being injected into your email body. This is industry standard. Whilst it makes for good analytics sometimes people may see drops in their campaigns deliverability.

This is due to the same “tracking” domain being used across 1000s of campaigns setup by all the users of the cold emailing software. ESPs (email service providers) are smart to understand that there’s millions of emails being opened and they’re all sending “requests” to the same “tracking url”. This may\* cause a slight drop in your deliverability.

So what’s the fix? Simple.

You trick the ESP by “masking” the tracking url with your own.

### Step 1:

Add a new email account / open an existing email account within smartlead

Scroll down to

Custom tracking domain

### Step 2:

Open your domain management tool e.g Godaddy, Namecheap, Crazydomains etc

Head over to the DNS management section

In your Host Records section add in a CNAME with the following

Type: CNAME Record

Host:

emailtracking

Value:

open.sleadtrack.com

TTL:

Automatic

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F8a8c8522-47bf-4e4a-9737-ba716d623cc7%2FScreen_Shot_2022-06-16_at_11.26.36_am.png?table=block&id=dbd2ea0c-75db-48dd-ae6f-28c1c1c4e9d8&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

Once this is done, wait for 30 mins to 24 hour to be bubbled to your account.

Now head over to your app and paste the full url into the text field like below in this format

http://{host}.{yourdomain}

In my case my domain is [getsmartwriter.co](http://getsmartwriter.co/) and my host is emailtracking

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fbb81818b-eb7d-43c5-8a4f-47009d7fe738%2FScreen_Shot_2022-06-16_at_11.22.48_am.png?table=block&id=b7b3c59f-89b2-49c5-a97e-59f35b6be9e5&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

#### Verify Your CNAME Tracking

If you’ve done thing’s right. Click on the “Verify CNAME” button. It’ll take you to a [nslookup.io](http://nslookup.io/) link.

If underneath the “Canonical name” it says “open.sleadtrack.com”, then you did it right.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F85070967-020b-482a-98f8-0cd242402e8f%2FScreen_Shot_2022-07-22_at_3.29.55_pm.png?table=block&id=79bca0ce-6b3c-4813-8681-d9ca788ebd90&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### Domain Tracking Tips

#### Combined tracking / Account level Tracking

If you have an aged domain, or a domain with good reputation, you can use that single domain for tracking, instead of setting up a custom tracking per email domain.

For e.g, if you have a well reputed / old domain named

smartlead.com

, you can do the CNAME process (listed above) to that domain and use [emailtracking.smartlead.com](http://emailtracking.smartlead.com/) across all the mailboxes in your Smartlead account.

So vaibhav@getsmartlead.com, v@usesmartlead.com etc will all have tracking point to

emailtracking.smartlead.com

This works well if you’re working with clients too, where you can condense tracking to a single domain.

#### Individual Tracking

If you’re running experiments, starting off fresh or want to build up the authority across multiple domains you can set up individual tracking per domain. Unlike the above configuration where a common tracking is shared across all your mailboxes, in this case you can have it siloed per account.

Using the above example:

For v@ [usesmartlead.com](http://usesmartlead.com/) the usesmartlead.com domain will need to have a CNAME configuration for

emailtracking

pointing to

open.sleadtrack.com

For vaibhav@getsmartlead.com the getsmartlead.com domain will need to have a CNAME configuration for

emailtracking

pointing to

open.sleadtrack.com

So on and so forth


---


## API Access To Everything

**URL:** https://help.smartlead.ai/API-Access-To-Everything-4ee6635a218a4d389d74380ba6db5c49


[Skip to content](https://help.smartlead.ai/API-Access-To-Everything-4ee6635a218a4d389d74380ba6db5c49#main)

![🤖 Page icon](<Base64-Image-Removed>)![🤖 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f916.svg)

# API Access To Everything

Date

July 19, 2022 → July 25, 2022

Assign

Empty

Status

Completed


---


## Full Create Campaign API Access

**URL:** https://help.smartlead.ai/Full-Create-Campaign-API-Access-45640a3e9eca4589b544330b51a65b96


[Skip to content](https://help.smartlead.ai/Full-Create-Campaign-API-Access-45640a3e9eca4589b544330b51a65b96#main)

![Page icon](https://help.smartlead.ai/icons/archery_gray.svg?mode=light)

# Full Create Campaign API Access

Date

November 3, 2022 → November 4, 2022

Assign

Empty

Status

Completed


---


## Full Webhook Reply Response

**URL:** https://help.smartlead.ai/Full-Webhook-Reply-Response-66e769287b114d93adf6eeec62a6d948


[Skip to content](https://help.smartlead.ai/Full-Webhook-Reply-Response-66e769287b114d93adf6eeec62a6d948#main)

# Full Webhook Reply Response

{"lead\_email":"andy@fortrasearch.com","lead\_name":"Andy","category":"Interested","lead\_category\_id":1,"campaign\_name":"Global \| Founder \| 0-4 Sales Employees","campaign\_id":3109,"from":"vaibhav@usesmartlead.com","to":"andy@fortrasearch.com","history":\[{"type":"SENT","time":"2022-11-10T12:30:55.748Z","email\_body":"<p>Hey <span data-type=\\"mention\\" >Andy</span>,<br><br>Saw that you lead ~3 person sales team.<br><br>We've built a tool that's helped my 1 SDR bring in 30k MRR in a few months.<br><br>Do you want to see if it can do the same for your team?<br><br>Mind if I send some more info?</p><p></p> <p>Thanks,<br><br>Vaibhav Namburi<br>Founder - <a target=\\"\_blank\\" rel=\\"noopener noreferrer nofollow\\" href=\\"http://Smartlead.ai\\">Smartlead.ai</a></p>","subject":"Andy - question?"},{"type":"REPLY","time":"2022-11-10T12:31:36.000Z","email\_body":"<p>Sure, that would be great!</p><p>Get Outlook for iOS&lt;<a href=\\"https://aka.ms/o0ukef\\">https://aka.ms/o0ukef</a>&gt;<br/>\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_<br/>From: Vaibhav &lt;<a href=\\"mailto:vaibhav@usesmartlead.com\\">vaibhav@usesmartlead.com</a>&gt;<br/>Sent: Thursday, November 10, 2022 7:30:55 AM<br/>To: Andy Grosso &lt;<a href=\\"mailto:andy@fortrasearch.com\\">andy@fortrasearch.com</a>&gt;<br/>Subject: Andy - question?</p><p>Hey Andy,</p><p>Saw that you lead ~3 person sales team.</p><p>We&rsquo;ve built a tool that&rsquo;s helped my 1 SDR bring in 30k MRR in a few months.</p><p>Do you want to see if it can do the same for your team?</p><p>Mind if I send some more info?</p><p>Thanks,</p><p>Vaibhav Namburi<br/>Founder - Smartlead.ai&lt;<a href=\\"http://Smartlead.ai\\">http://Smartlead.ai</a>&gt;</p>"},{"time":"2022-11-10T22:47:13.814+00:00","type":"SENT","email\_body":"<p>Hey Andy<br><br>Sounds great.<br><br>Would you be open to booking a time here <a target=\\"\_blank\\" rel=\\"noopener noreferrer nofollow\\" href=\\"http://cal.com/vaibhav-n\\">cal.com/vaibhav-n</a>&nbsp;?</p>"},{"time":"2022-11-10T22:47:57+00:00","type":"REPLY","email\_body":"Yes, that would be great.\\n\\nGet Outlook for iOS<https://aka.ms/o0ukef>"},{"time":"2022-11-11T05:58:28.211+00:00","type":"SENT","email\_body":"<p>Epic!<br><br>Thanks Andy! Looking forward to chatting</p>"}\],"lastReply":{"time":"2022-11-10T22:47:57+00:00","type":"REPLY","email\_body":"Yes, that would be great.\\n\\nGet Outlook for iOS<https://aka.ms/o0ukef>"},"event\_type":"LEAD\_CATEGORY\_UPDATED"}

​


---


##  Webhooks

**URL:** https://help.smartlead.ai/Webhooks-77eb52d5d1c0445d8428008892aaa655


[Skip to content](https://help.smartlead.ai/Webhooks-77eb52d5d1c0445d8428008892aaa655#main)

![](https://help.smartlead.ai/images/page-cover/met_silk_kashan_carpet.jpg)

# ![🪝](<Base64-Image-Removed>) Webhooks

Date

June 20, 2022

Assign

Empty

Status

Completed


---


## /  A/B Testing

**URL:** https://help.smartlead.ai/A-B-Testing-692e60cd855b430fb973855d354d54e0


[Skip to content](https://help.smartlead.ai/A-B-Testing-692e60cd855b430fb973855d354d54e0#main)

# ![🅰️](<Base64-Image-Removed>)/ ![🅱️](<Base64-Image-Removed>) A/B Testing

Date

July 4, 2022 → July 11, 2022

Assign

Empty

Status

Completed


---


## Event’s Include:

**URL:** https://help.smartlead.ai/Event-s-Include-a8959d234e984b63b25bb9f6fed28539


[Skip to content](https://help.smartlead.ai/Event-s-Include-a8959d234e984b63b25bb9f6fed28539#main)

# Event’s Include:

\- Email sent
\- Email opened
\- Email replied
\- Link clicked
\- Lead unsubscribed
\- Campaign completed

Each event will send a JSON body containing specific data to that event. That information is as such:

EMAIL\_OPENED:

{
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_opened: <time email was opened>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
}

​

EMAIL\_SENT:

{
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_sent: <time email was sent>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
}

​

EMAIL\_REPLIED:

{
event\_type:"EMAIL\_REPLY"
subject: <subject>
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_replied: <time email was replied to>
reply\_body: <copy of the reply from the lead in full copy (html if there is)>
preview\_text: <copy of the latest reply in plain text>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
sequence\_number: <the sequence number that triggered this event>
}

​

LINK\_CLICKED:

{
from\_email: <mailbox used>
to\_email: <lead email>
to\_name: <lead name>
time\_clicked: <time link was clicked>
link\_clicked: <which link was clicked>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
}

​

LEAD\_UNSUBSCRIBED:

{
lead\_email: <email of lead that unsubscribed>
campaign\_name: <name of the campaign this event belongs to>
campaign\_id: <campaign id for your personal identification>
}

​

CATEGORY\_UPDATED:

{"lead\_email":"ramesh@five2one.com.au","lead\_name":"Ramesh","category":"Interested","lead\_category\_id":1,"campaign\_name":"GOauth Testing 1","campaign\_id":750}

​


---


## Common Email Errors

**URL:** https://help.smartlead.ai/Common-Email-Errors-9273cbc0ce17483b9479e4c99cf284fa


[Skip to content](https://help.smartlead.ai/Common-Email-Errors-9273cbc0ce17483b9479e4c99cf284fa#main)

![🌡️ Page icon](<Base64-Image-Removed>)![🌡️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f321-fe0f.svg)

# Common Email Errors

[Email has been blocked due to security reasons](https://help.smartlead.ai/Email-has-been-blocked-due-to-security-reasons-d537022952a746bea23afc216a523908?pvs=25)

[Google Error - Invalid login: 534-5.7.9 Application-specific password required.](https://help.smartlead.ai/Google-Error-Invalid-login-534-5-7-9-Application-specific-password-required-4e3c7962cd4a4f57868bffb5d62d4129?pvs=25)

[Data command failed: 550 5.4.5 Daily user sending quota exceeded.](https://help.smartlead.ai/Data-command-failed-550-5-4-5-Daily-user-sending-quota-exceeded-1a89be4d3e5543b89b41cce9ee496a73?pvs=25)

[Why am I getting a ‘Connection Timed Out’ error?](https://help.smartlead.ai/Why-am-I-getting-a-Connection-Timed-Out-error-bbe68c07d5e64d2582a31780f708bd02?pvs=25)


---


## Image Personalisation

**URL:** https://help.smartlead.ai/Image-Personalisation-7f7f88c82bf1431b97c5a146ba2d07e5


[Skip to content](https://help.smartlead.ai/Image-Personalisation-7f7f88c82bf1431b97c5a146ba2d07e5#main)

![🖼️ Page icon](<Base64-Image-Removed>)![🖼️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f5bc-fe0f.svg)

# Image Personalisation

Date

May 17, 2023 → May 31, 2023

Assign

Empty

Status

Empty


---


## Email has been blocked due to security reasons

**URL:** https://help.smartlead.ai/Email-has-been-blocked-due-to-security-reasons-d537022952a746bea23afc216a523908


[Skip to content](https://help.smartlead.ai/Email-has-been-blocked-due-to-security-reasons-d537022952a746bea23afc216a523908#main)

# Email has been blocked due to security reasons

Please contact your admin to unblock your account

But you are the admin.

To unblock a blocked account (once the reason for the block has been rectified), log in to the Admin Console. Navigate to Users in the left pane.Click on the Filter button, choose Blocked Users from the drop-down. The accounts of blocked users will be listed. You can unblock an individual user by clicking the Blocked icon or select the users you want to unblock and click Unblock from the top

Learn more [here](https://www.zoho.com/mail/help/adminconsole/user-settings.html#Block)


---


## Email Templates

**URL:** https://help.smartlead.ai/Email-Templates-d598c6ac9eb34a9e95a0eaceceea1a74


[Skip to content](https://help.smartlead.ai/Email-Templates-d598c6ac9eb34a9e95a0eaceceea1a74#main)

![🎞️ Page icon](<Base64-Image-Removed>)![🎞️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f39e-fe0f.svg)

# Email Templates

Date

November 28, 2022 → November 30, 2022

Assign

Empty

Status

Completed


---


## Google Error - Invalid login: 534-5.7.9 Application-specific password required.

**URL:** https://help.smartlead.ai/Google-Error-Invalid-login-534-5-7-9-Application-specific-password-required-4e3c7962cd4a4f57868bffb5d62d4129


[Skip to content](https://help.smartlead.ai/Google-Error-Invalid-login-534-5-7-9-Application-specific-password-required-4e3c7962cd4a4f57868bffb5d62d4129#main)

# Google Error - Invalid login: 534-5.7.9 Application-specific password required.

If you receive this error when attempting to connect your inbox to the platform, learn how you can resolve it.

If you are receiving this error, it indicates that you have 2 factor authentication enabled under the inbox you are attempting to connect, and will need to create an App password under your Google account in order to get it connected to the platform. In order to create an app password, please follow our guide on how to do this


---


## Data command failed: 550 5.4.5 Daily user sending quota exceeded.

**URL:** https://help.smartlead.ai/Data-command-failed-550-5-4-5-Daily-user-sending-quota-exceeded-1a89be4d3e5543b89b41cce9ee496a73


[Skip to content](https://help.smartlead.ai/Data-command-failed-550-5-4-5-Daily-user-sending-quota-exceeded-1a89be4d3e5543b89b41cce9ee496a73#main)

# Data command failed: 550 5.4.5 Daily user sending quota exceeded.

This means your daily limit for your email account (gmail, zoho, outlook) has been exceeded.

Check with your email providers daily limits and increase it if possible.

Ideally if you get this message, you should give this email address a break for 1-2 days to prevent future blocks.

Steps:

Go to your existing campaign, click the edit button

Top right, select the settings button (the cog wheel)

In the SMTP tab, untick the email address causing issues

Click save and voila


---


## Global Block List

**URL:** https://help.smartlead.ai/Global-Block-List-6fb48f37f88e4e3ebafbe77b47b33eb8


[Skip to content](https://help.smartlead.ai/Global-Block-List-6fb48f37f88e4e3ebafbe77b47b33eb8#main)

![✋🏾 Page icon](<Base64-Image-Removed>)![✋🏾 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/270b-1f3fe.svg)

# Global Block List

Date

July 25, 2022 → July 28, 2022

Assign

Empty

Status

Completed


---


## AI Email Account Warmups

**URL:** https://help.smartlead.ai/AI-Email-Account-Warmups-da0451c052184725ad8e3c73f7ee1a82


[Skip to content](https://help.smartlead.ai/AI-Email-Account-Warmups-da0451c052184725ad8e3c73f7ee1a82#main)

![🤑 Page icon](<Base64-Image-Removed>)![🤑 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f911.svg)

# AI Email Account Warmups

Warm up engines protect your emails from landing in spam and build your sender reputation.

Smartlead’s unique algorithm is built to emulate a humanized sending behaviour that ensures your reputation consistently improves - therefore landing more of your emails in your leads inbox, not spam.

In addition, Smartlead, “manually” moves emails that land in spam to the primary inbox, marks them as important and ensures a priority reply to that email.

Bounce protection automatically delists email accounts from the warmup pool to consistently protect your sender reputation.

You will join an industry leading email pool containing aged domains, high reputation domains across Zoho, Gmail, Outlook etc.

The start process is simple. Once you’ve added an email account (guides [here](https://help.smartlead.ai/72dbf70748a8475287240dc1a2221418#a231ad3e0756458e8fa87646ac6c2717)) Follow these steps:

1) Head over to Email Accounts on the left

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Ff109e3f2-60a9-469c-82d3-6c1631c29aba%2FScreen_Shot_2022-06-24_at_6.05.37_pm.png?table=block&id=066480f1-fae6-494b-8e36-fe2a25c8cfeb&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=290&userId=&cache=v2)

2) Select the email account you want to enable warm up by clicking on it

3) Select your configuration (scroll down for more about this)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fa3ed8d2e-94aa-427c-97b7-f13a1d2ad425%2FScreen_Shot_2022-06-24_at_6.07.56_pm.png?table=block&id=516c5cac-6652-4e2c-ab0e-85f34b89118e&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

4) “Enable Warmup” and click Save and voila, Smartlead will automatically kick off in the background ensuring your emails always stay out of spam.

5) You can review the statistics of your warm up emails each day (give it a couple of minutes to kick off)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fe4bd29c7-17ac-4f91-a5f9-f3c4a3ced275%2FScreen_Shot_2022-06-24_at_6.07.35_pm.png?table=block&id=2e7ec7d8-1a7e-4c61-9337-194bb517df2e&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### Configuration Explanation:

#### Total daily emails

This is the total number of emails you want your warm up account to send each day. If you’re running an active campaign with this email account, it would be recommended to keep this number to 10-20, and bump it up once the active campaign is finished.

#### Daily Ramp up

If you’ve got a fresh domain, turn this option on. It naturally progresses the number of emails you send each day. This prevents Email Service Provides (Gmail, Zoho etc…) from flagging your account for unusual activity.

However if your domain is already warmed up or if you’re coming from another warm up engine, you do not need to enable this option

#### Randomise Warmup numbers

Uses trained algorithms to emulate human sending patterns between the thresholds you select. This improves the deliverability and prevents systems to picking up that it’s being done algorithmically.

#### Reply Rate

Defines the number of emails your email account will be replying to. Naturally, you don’t reply to each email you receive (we all get spam, newsletters, promos etc).

A healthy 20-30% reply rate has proven to boost deliverability and reputation significantly.

Above 30% is not recommended unless you are an expert in this field and know what you’re doing.


---


## Liquid Syntax

**URL:** https://help.smartlead.ai/Liquid-Syntax-ea1d25edb3594c92b7f08998c4ab50f9


[Skip to content](https://help.smartlead.ai/Liquid-Syntax-ea1d25edb3594c92b7f08998c4ab50f9#main)

![🌊 Page icon](<Base64-Image-Removed>)![🌊 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f30a.svg)

# Liquid Syntax

Date

November 10, 2022 → November 14, 2022

Assign

Empty

Status

Completed


---


##  Whitelabel Clients Given Credits 

**URL:** https://help.smartlead.ai/Whitelabel-Clients-Given-Credits-f829a4fecd414851a20f3080466fd6b6


[Skip to content](https://help.smartlead.ai/Whitelabel-Clients-Given-Credits-f829a4fecd414851a20f3080466fd6b6#main)

![🏜️ Page icon](<Base64-Image-Removed>)![🏜️ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f3dc-fe0f.svg)

# Whitelabel Clients Given Credits

Date

March 21, 2023 → March 28, 2023

Assign

Empty

Status

Empty

Allow users to dedicate certain number of credits / emails per client.


---


##  Dedicated IP access

**URL:** https://help.smartlead.ai/Dedicated-IP-access-8fd4caa924c24376b1771ee6893240f7


[Skip to content](https://help.smartlead.ai/Dedicated-IP-access-8fd4caa924c24376b1771ee6893240f7#main)

# ![💻](<Base64-Image-Removed>) Dedicated IP access

Date

October 3, 2022 → October 5, 2022

Assign

Empty

Status

Empty


---


## Zapier Setup (beta)

**URL:** https://help.smartlead.ai/Zapier-Setup-beta-14e16cbeab97415ab7f2927592978bd6


[Skip to content](https://help.smartlead.ai/Zapier-Setup-beta-14e16cbeab97415ab7f2927592978bd6#main)

![📟 Page icon](<Base64-Image-Removed>)![📟 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f4df.svg)

# Zapier Setup (beta)

### Using Zapier To Add Leads To A Campaign

Using Zapier To Add Leads To A Campaign

[Using Zapier To Add Leads To A Campaign](https://www.loom.com/share/dd842885ebc54a589ea2b258dc9fae03 "Using Zapier To Add Leads To A Campaign")

1.38K views

Copy link

[Open video in Loom](https://www.loom.com/share/dd842885ebc54a589ea2b258dc9fae03)

13

1.2×

6 min⚡️7 min 36 sec6 min 5 sec5 min 4 sec4 min 3 sec3 min 34 sec3 min 2 sec2 min 26 sec

![](https://cdn.loom.com/sessions/thumbnails/dd842885ebc54a589ea2b258dc9fae03-00001.jpg)

Your user agent does not support the HTML5 Video element.

[Using Zapier To Add Leads To A Campaign](https://www.loom.com/share/dd842885ebc54a589ea2b258dc9fae03 "Using Zapier To Add Leads To A Campaign")

1.38K views

Copy link

[Open video in Loom](https://www.loom.com/share/dd842885ebc54a589ea2b258dc9fae03)

13

1.2×

6 min⚡️7 min 36 sec6 min 5 sec5 min 4 sec4 min 3 sec3 min 34 sec3 min 2 sec2 min 26 sec

13 Comments

![Vaibhav Namburi](https://cdn.loom.com/avatars/898428_43d62e1476d6407981125ff799bbb3da_192.jpg)

Vaibhav Namburi1:24

Aug 25, 2022

Click on Webhooks By Zapier

![Vaibhav Namburi](https://cdn.loom.com/avatars/898428_43d62e1476d6407981125ff799bbb3da_192.jpg)

Vaibhav Namburi

July 24, 2023

👍

Reply

![Tyler Brown](https://cdn.loom.com/avatars/28058853_6d87266e0e374104a1a1df9b8901d525_192.jpg)

Tyler Brown4:51

Apr 3, 2024

Any ETA on a SmartLead/Zapier integration? Working with their JSON editor is PAINFUL

1 more reply

![Vaibhav Namburi](https://cdn.loom.com/avatars/898428_43d62e1476d6407981125ff799bbb3da_192.jpg)

Vaibhav Namburi

Apr 10, 2024

I agree it is a pain, no ETA just yet

![Stephen Smeke](https://cdn.loom.com/avatars/1527480_5c622f4c1c1f4b6b92e8e8cd0df56b09_192.jpg)

Stephen Smeke

May 28, 2025

🙏

![Heiko Heil](https://avatar-management--avatars.us-west-2.prod.public.atl-paas.net/70121:92c63592-ebd2-492e-8e2f-f042225a5a13/800d97f4-298a-436c-b38b-2add5d3c6c1c/128)

Heiko Heil

Nov 21, 2025

Cant understand why its not available - anyone on Fiverr would do it for a few bucks as API is there already...

Reply

![Issam Chafi](https://cdn.loom.com/avatars/18928640_600ea4e0b50a43638e9978d61dd5140b_192.jpg)

Issam Chafi6:05

Dec 22, 2022

Thank you Vaibhav! 🙏

![Vaibhav Namburi](https://cdn.loom.com/avatars/898428_43d62e1476d6407981125ff799bbb3da_192.jpg)

Vaibhav Namburi

July 24, 2023

🙌

Reply

![R K](https://cdn.loom.com/avatars/16362327_0f433975dada495e8b436979a7474650_192.jpg)

R K6:05

Mar 28, 2023

Thank you Vaibhav! 🙏

![Vaibhav Namburi](https://cdn.loom.com/avatars/898428_43d62e1476d6407981125ff799bbb3da_192.jpg)

Vaibhav Namburi

July 24, 2023

🙌

Reply

![David Puyandayev](https://cdn.loom.com/avatars/15175771_50b822d65b52465a9081c8fcb4ea2778_192.jpg)

David Puyandayev6:05

July 24, 2023

Thank you Vaibhav! 🙏

![Vaibhav Namburi](https://cdn.loom.com/avatars/898428_43d62e1476d6407981125ff799bbb3da_192.jpg)

Vaibhav Namburi

July 24, 2023

🙌

Reply

![Andrew Tamplin](https://cdn.loom.com/avatars/16110827_3fede1e0979749fb92749d0bd62691f1_192.jpg)

Andrew Tamplin6:05

July 30, 2023

Thank you Vaibhav! 🙏

Reply

### Using Zapier To Listen To Events From SmartLead


---


##  Agency Views

**URL:** https://help.smartlead.ai/Agency-Views-97fe6d0515754347a4ea328cac50527c


[Skip to content](https://help.smartlead.ai/Agency-Views-97fe6d0515754347a4ea328cac50527c#main)

# ![🏝](<Base64-Image-Removed>) Agency Views

Date

August 8, 2022 → August 19, 2022

Assign

Empty

Status

Completed


---


## Agency View & Client Access

**URL:** https://help.smartlead.ai/Agency-View-Client-Access-bdc1b09947af483981752eb57b3c6711


[Skip to content](https://help.smartlead.ai/Agency-View-Client-Access-bdc1b09947af483981752eb57b3c6711#main)

![👥 Page icon](<Base64-Image-Removed>)![👥 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f465.svg)

# Agency View & Client Access

If you run an agency this is a fantastic way to invite your clients to view their campaigns and remove all the hassle in sending them daily reports.

They get to see your incredible work, live!

You can offer this option as an additional premium and charge them more without costing you a single dollar extra

### 1) Click on Add Client

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F93af0e63-7872-4615-ac0c-8203a70811af%2FScreen_Shot_2022-08-29_at_3.38.23_pm.png?table=block&id=3ae8d150-3fb7-47be-bef2-5122e302efdf&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### 2) Add your clients details and your Company’s Name (which will show up on your clients UI

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fc698a3df-0898-47de-9fe8-d6bae7bb94f4%2FScreen_Shot_2022-08-29_at_3.41.00_pm.png?table=block&id=335f3aad-d544-4677-8022-22a3efc32ba2&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### 3) Your client will get invited to login

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F9b8f2f13-2b55-4e48-aea7-2919619d126b%2FScreen_Shot_2022-08-29_at_3.42.39_pm.png?table=block&id=e2c2ebb2-c8ca-4ca3-9aa3-ac134dc3f27a&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

### 4) Add clients to a campaign/email account

If you’re creating a fresh campaign, you can select a client in the General Settings of a campaign

If you’ve already created a campaign, click on the 3 dots in the main dashboard, and allocate the campaign to the client

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F2176fcfe-fc4f-4b89-9b10-f7a689083106%2FScreen_Shot_2022-08-29_at_3.45.21_pm.png?table=block&id=202e0e4d-828a-4e35-b4ab-9703cb601928&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=290&userId=&cache=v2)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F7f9563c9-18c5-4643-909e-3c4d7c6ca186%2FScreen_Shot_2022-08-29_at_3.48.20_pm.png?table=block&id=be28b622-5d76-40af-ad6a-a73962da8e2d&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=770&userId=&cache=v2)

Similarly so, you can associate an email account to a client in the email account management settings section.

And thats it, when your client logs in they’ll only see the email accounts and campaigns associated to them


---


## Microsoft oAuth

**URL:** https://help.smartlead.ai/Microsoft-oAuth-ed449ed6f0394aafaa1e682b9798f59c


[Skip to content](https://help.smartlead.ai/Microsoft-oAuth-ed449ed6f0394aafaa1e682b9798f59c#main)

![](https://help.smartlead.ai/images/page-cover/solid_yellow.png)

![🔬 Page icon](<Base64-Image-Removed>)![🔬 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f52c.svg)

# Microsoft oAuth

Date

October 11, 2022 → October 18, 2022

Assign

Empty

Status

Completed


---


## Webhook Guide Updated 

**URL:** https://help.smartlead.ai/Webhook-Guide-Updated-4d0ae6b2fa6a4db1b4c1ead824a86866


[Skip to content](https://help.smartlead.ai/Webhook-Guide-Updated-4d0ae6b2fa6a4db1b4c1ead824a86866#main)

![🛻 Page icon](<Base64-Image-Removed>)![🛻 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f6fb.svg)

# Webhook Guide Updated

Please use these guides as your webhook reference. If you’ve already built infrastructure on Smartlead, review all the docs, observe the “deprecated fields” update your systems to use the “new fields” by 1st January 2024.

For new users please use the “new fields” in your setup and use the “Test Webhook” on the UI to get the defined sample response.

[Lead Category Updated](https://help.smartlead.ai/Lead-Category-Updated-22cab06ce4a0499ca417916cececa62c?pvs=25)

[Email Bounce](https://help.smartlead.ai/Email-Bounce-3c44b5bd92234b02ba2c9e42542b0e9a?pvs=25)

[Link Clicked](https://help.smartlead.ai/Link-Clicked-afd2fb5f11164db986bf5cef251825de?pvs=25)

[Lead Unsubscribed](https://help.smartlead.ai/Lead-Unsubscribed-5b21eed0deac40fc84190b46d963ce4e?pvs=25)

[Email Opened](https://help.smartlead.ai/Email-Opened-466fc579d2d942a688d52ec51b6e0ae6?pvs=25)

[Email Sent](https://help.smartlead.ai/Email-Sent-d178e38d71a24e24a92383b7222d46c2?pvs=25)

[Email Replied](https://help.smartlead.ai/Email-Replied-aeebacc09db9456fbf23dcf5c6cbd0fd?pvs=25)

[Threaded Replies](https://help.smartlead.ai/Threaded-Replies-ff92a607c93645b7b1568d8219218423?pvs=25)

[Campaign Status Change](https://help.smartlead.ai/Campaign-Status-Change-6c6fe98602b346aebdaf7c2ff9bae7e7?pvs=25)

[Untracked replies](https://help.smartlead.ai/Untracked-replies-d68b21be42c74f50b7f86bc63103a1c6?pvs=25)

[Manual Step Reached](https://help.smartlead.ai/Manual-Step-Reached-99aa4a20e2e247c3865f53f11c1a4b20?pvs=25)


---


## Gmail oAuth

**URL:** https://help.smartlead.ai/Gmail-oAuth-c316128bed1649368d74f59befa54fb5


[Skip to content](https://help.smartlead.ai/Gmail-oAuth-c316128bed1649368d74f59befa54fb5#main)

![⚡ Page icon](<Base64-Image-Removed>)![⚡ Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/26a1.svg)

# Gmail oAuth

Date

January 3, 2023 → January 15, 2023

Assign

Empty

Status

Completed


---


## Buying and Setting Up A Zoho Account

**URL:** https://help.smartlead.ai/Buying-and-Setting-Up-A-Zoho-Account-00146eec31af43988538284c921208bc


[Skip to content](https://help.smartlead.ai/Buying-and-Setting-Up-A-Zoho-Account-00146eec31af43988538284c921208bc#main)

# Buying and Setting Up A Zoho Account

1) Buy a domain from namecheap, crazydomains, godaddy etc.

2) Sign up to [zoho business email](https://www.zoho.com/mail/)

3) Once sign up is completed, you can add multiple “managed” domains under your primary owned account

4) Click on your profile photo on the top right and click on on Admin Console

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fda47649d-0335-4781-bb37-81472851e847%2FScreen_Shot_2022-06-28_at_3.59.03_pm.png?table=block&id=5c899a9c-17b8-4123-8fb5-a7aef395ab26&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=480&userId=&cache=v2)

5) Click on the “Domains” tab in the left panel, direct link [here](https://mailadmin.zoho.com.au/cpanel/home.do#domains/list)

6) Click on the Add dropdown and type in your newly purchased (or existing) domain address

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Ff6c61dbf-84fa-4453-ba36-94ed4995e217%2FScreen_Shot_2022-06-28_at_4.00.14_pm.png?table=block&id=6324bab8-1c62-40bf-a246-6e58158f57f9&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=860&userId=&cache=v2)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fa4846808-c14b-4748-afb0-7b2fbc6df5c8%2FScreen_Shot_2022-06-28_at_4.01.41_pm.png?table=block&id=59c32358-0c28-45b1-8048-619f292bc472&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=770&userId=&cache=v2)

7) You’ll need to verify ownership of this domain.

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F5f9c760c-a6ce-4855-b7bf-f4dc09d74086%2FScreen_Shot_2022-06-28_at_4.09.19_pm.png?table=block&id=c430b9f6-6270-4bba-8ad0-ac5dbe306f06&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=960&userId=&cache=v2)

8) Paste the data in the appropriate fields in your domain registration service (namecheap etc)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2F760631d1-8577-42a9-9016-aa2ba2f51288%2FScreen_Shot_2022-06-28_at_4.10.03_pm.png?table=block&id=a12e08b5-9ac9-4696-aba4-019b21dea4a8&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

9) Wait 15-30 minutes

10) Then you you’ll need to add MX records to your DNS. In your DNS in the Mail Settings section, select “Custom MX” from the dropdown and add in the values zoho provides (similar to below)

![](https://help.smartlead.ai/image/https%3A%2F%2Fs3-us-west-2.amazonaws.com%2Fsecure.notion-static.com%2Fa6b76b36-5c4f-4bb6-b763-4c329a223e9f%2FScreen_Shot_2022-06-28_at_4.11.12_pm.png?table=block&id=8751fab7-a1a0-46ef-ad02-7557db4e5f43&spaceId=cf510dbd-b411-4490-8576-0c09338b7646&width=2000&userId=&cache=v2)

11) This should do the trick and you’re good to go.

12) For boosting deliverability, you can continue to add the SPF and DKIM records.

13) These are both TXT fields, and you simply just copy the values given in zoho into the DNS

14) Wait 30 min - 2 hours for this to verify, but you can start sending emails if you’d like to.


---


## Global lead list management

**URL:** https://help.smartlead.ai/Global-lead-list-management-e4fa501383074dfebe65a6c24307780c


[Skip to content](https://help.smartlead.ai/Global-lead-list-management-e4fa501383074dfebe65a6c24307780c#main)

![🪐 Page icon](<Base64-Image-Removed>)![🪐 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1fa90.svg)

# Global lead list management

Date

March 20, 2023 → March 22, 2023

Assign

Empty

Status

Empty


---


## Untracked replies

**URL:** https://help.smartlead.ai/Untracked-replies-d68b21be42c74f50b7f86bc63103a1c6


[Skip to content](https://help.smartlead.ai/Untracked-replies-d68b21be42c74f50b7f86bc63103a1c6#main)

# Untracked replies

Response Structure

{"event\_timestamp":"","reply\_message":{"message\_id":"","html":"","text":"","time":""},"secret\_key":"","description":"","sender\_detail":"","recipient\_detail":"","cc":"","bcc":"","subject":"","visible\_text":"","has\_attachment":false,"metadata":{"webhook\_created\_at":""},"webhook\_url":"","webhook\_id":11,"webhook\_name":"","event\_type":""}

​

Example Response

{"event\_timestamp":"2024-04-17T05:24:33.353Z","reply\_message":{"message\_id":"<CAJZgRaRf=B4WEPmv4gujBNmJE46XpNbWiN7V\_DHsAvyvqgEpDg@mail.gmail.com>","html":"","text":"Hi\\n","time":"2024-04-17T05:24:33.353Z"},"secret\_key":"e0207d40-84ef-4ad6-89eb-7dbff8c0138d","description":"","sender\_detail":"sunita soy <sunita1991soy@gmail.com>","recipient\_detail":"sukhvir@smartlead.ai","cc":"","bcc":"","subject":"Untracked replies","visible\_text":"Hi\\n","has\_attachment":false,"metadata":{"webhook\_created\_at":"2024-04-12T13:51:26.269Z"},"webhook\_url":"https://webhook.site/05076ec5-99ab-4277-b223-293df0b402e9","webhook\_id":94,"webhook\_name":"test","event\_type":"UNTRACKED\_REPLIES"}

​

event\_timestamp : When this email was tracked in UTC

message\_id: Message ID of the reply

html: HTML copy of the message

text: Text copy (With HTML parsed) of the message

time: Time of receiving the event

secret\_key: Used to protect your endpoints

description: If any description

sender\_detail: Details of the person who sent email

recipient\_detail: Your leads email

cc: Anyone Cc’ed

bcc: Anyone Bcc’ed

subject: Subject of the email sent

visible\_text: Usually the preview text or plain message body

has\_attachment: Boolean for if they have a file attached

webhook\_created\_at: When the webhook was created

webhook\_url: Endpoint for the webhook

webhook\_id: Smartlead allocated webhook ID

webhook\_name: Name given to webhook

event\_type: Name of event occurred


---


## Custom CRM

**URL:** https://help.smartlead.ai/Custom-CRM-bd7c9250607e402a8ee881a50a2ef2c7


[Skip to content](https://help.smartlead.ai/Custom-CRM-bd7c9250607e402a8ee881a50a2ef2c7#main)

![💼 Page icon](<Base64-Image-Removed>)![💼 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f4bc.svg)

# Custom CRM

Date

April 21, 2023 → November 11, 2023

Assign

Empty

Status

Empty


---


## Lead Category Updated

**URL:** https://help.smartlead.ai/Lead-Category-Updated-22cab06ce4a0499ca417916cececa62c


[Skip to content](https://help.smartlead.ai/Lead-Category-Updated-22cab06ce4a0499ca417916cececa62c#main)

# Lead Category Updated

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"webhook\_url":"","lead\_id":"""event\_type":"LEAD\_CATEGORY\_UPDATED","created\_at":"", ---\> new field"event\_timestamp":"", ---\> new field"from":"" ---\> Deprecate and instead use \`from\_email\`"from\_email":"", new field use instead of \`from\`"to":"", ---\> Deprecate and instead use \`to\_email\`
"lead\_email":"", ---\> Deprecate and instead use \`to\_email\`
"to\_email":"", new field use instead of \`to\` and \`lead\_email\`"lead\_name":"", ---\> Deprecate and instead use \`to\_name\`"to\_name":"",new field use instead of \`lead\_name\`"campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"category":"", ---\> Deprecate and instead use \`lead\_category.new\_name\`
"lead\_category\_id":"",---\> Deprecate and instead use \`lead\_category.new\_id\`"lead\_category":{"old\_id":"", ---\> new field
"old\_name":"", ---\> new field
"new\_id":"" ---\> new field use instead of \`lead\_category\_id\`
"new\_name":"", ---\> new field use instead of \`category\`
},"lead\_data":{"email":"","first\_name":"Ramesh","linkedin\_profile":"linkedin.com","custom\_fields":{ first\_line:"Super massive black hole"},"last\_name":"Kumar","phone\_number":"23454212","company\_name":"Smartlead","website":"smartlead.ai","location":"global","company\_url":"smartlead.ai",},"history":\[{\
stats\_id:"",\
type: ",\
message\_id:"",\
time:"",\
email\_body:"",\
subject:"",}\],"lastReply":{
stats\_id:"",
type:"",
message\_id:"",
time:"",
email\_body:""}// Deprecte and instead use \`last\_reply\` (renamed for standardisation)"last\_reply":{
stats\_id:"",
type:"",
message\_id:"",
time:"",
email\_body:""}"client\_id":"", ---\> new field
"secret\_key":"","app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecte and instead use \`app\_url\`,"description":"", ---\> new field"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"campaign\_status":"STOPPED","client\_id":null,"lead\_id":100,"lead\_email":"test@gmail.com","lead\_name":"Bob","lead\_data":{"email":"test@gmail.com","first\_name":"Bob","last\_name":"Jon","phone\_number":"9090887755","company\_name":"Five2One","website":"www.five2one.com.au","location":"India","custom\_fields":{"role":"Softwate Engineer","lead\_guid":"guid","undefined":1,"integration\_lead\_unique\_id":null,"227f554e-9e92-44d0-a175-9d5d703c6121":1,"3877eb8c-2f0a-4547-bc7d-0dcd153c0d79":1,"d1f90358-ca04-4c30-9347-a6a75cf2cc96":1,"e81322da-458a-4ddd-9d9f-b9011ca3aaaf":1},"linkedin\_profile":"https://www.linkedin.com/in/profile\_name/","company\_url":"","category":{"name":"Interested","sentiment\_type":"positive"}},"category":"Interested","lead\_category\_id":1,"lead\_category":{"old\_id":null,"old\_name":null,"new\_id":1,"new\_name":"Interested"},"campaign\_name":"test","campaign\_id":10,"from\_email":"test@gmail.com","to":"test@gmail.com","to\_email":"test@gmail.com","to\_name":"John","history":\[{"stats\_id":"id","type":"SENT","message\_id":"<id@five2one.com.au>","time":"2023-08-25T08:28:06.619Z","email\_body":"<div>Testing email</div>","subject":"Test Email 1"},{"stats\_id":"id","type":"REPLY","message\_id":"<id@mail.gmail.com>","time":"2023-08-25T08:32:45.000Z","email\_body":"<div>Testing email</div>"},{"stats\_id":"id","time":"2023-08-28T13:12:07+00:00","type":"REPLY","email\_body":"<div>Testing email</div>","message\_id":"<id1@mail.gmail.com>"}\],"lastReply":{"time":"2023-08-28T13:12:07+00:00","type":"REPLY","email\_body":"<div>Testing email</div>","message\_id":"<id1@mail.gmail.com>"},"last\_reply":{"time":"2023-08-28T13:12:07+00:00","type":"REPLY","email\_body":"<div>Testing email</div>","message\_id":"<id1@mail.gmail.com>"},"secret\_key":"secretkey","app\_url":"https://app.smartlead.ai/app/master-inbox","ui\_master\_inbox\_link":"https://app.smartlead.ai/app/master-inbox","description":"Lead - test@gmail.com category updated to Interested for campaign - test","metadata":{"webhook\_created\_at":"2023-09-26T11:02:01.385Z"},"webhook\_url":"https://webhook.site/5168fa12-0f49-45ta-81ss-1522da474a77","webhook\_id":100,"webhook\_name":"Ramesh Test","event\_type":"LEAD\_CATEGORY\_UPDATED"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

lead\_id:

event\_type: type of the event

event\_timestamp: The replied time

from: Deprecate it and instead use

from\_email

from\_email: mailbox used

to: Deprecate it and instead use

to\_email

lead\_email: Deprecate it and instead use

to\_email

to\_email: lead email

lead\_name: Deprecate it and instead use

to\_name

to\_name: lead name

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

category: Deprecate it and instead use

lead\_category.new\_name

lead\_category\_id: Deprecate it and instead use

lead\_category.new\_id

lead\_category

old\_id

old\_name

new\_id

new\_name

lead\_data:

history:

lastReply: Deprecate it and instead use

last\_reply

last\_reply:

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Email Bounce

**URL:** https://help.smartlead.ai/Email-Bounce-3c44b5bd92234b02ba2c9e42542b0e9a


[Skip to content](https://help.smartlead.ai/Email-Bounce-3c44b5bd92234b02ba2c9e42542b0e9a#main)

# Email Bounce

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"webhook\_url":"","stats\_id":"","event\_type":"EMAIL\_BOUNCE","created\_at":"", ---\> new field"time\_sent":"", ---\> Deprecate and instead use \`event\_timestamp\`"event\_timestamp":"", ---\> new field use instead of \`time\_sent\`"from\_email":"","to\_email":"","to\_name":"","custom\_subject":"", --\> Deprecated instead use subject
"custom\_email\_message":"", --\> Deprecated instead use \`sent\_message.html\`"subject":"","campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"sequence\_number":"","sent\_message\_body":"", ---\> Deprecate and instead use \`sent\_message.html\`"sent\_message":{"message\_id":"", ---\> new field for replacing \`message\_id\`"html":"", ---\> new field use instead of \`sent\_message\_body\`
"text":"" ---\> new field
"time":"" ---\> new field }"message\_id":"", ---\> Deprecate and instead use \`sent\_message.message\_id\`"client\_id":"", ---\> new field"app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`
"is\_bounced":true,---\> Deprecte the field becuase only true the event is triggered"bounce\_reply\_message\_id": <Bounced message ID>, ---\> Deprecte the field and use \`bounce\_message.message\_id\`
"bounce\_reply\_email": <Bounced full email>, ---\> Deprecte the field and use \`bounce\_message.html\`
"bounce\_reply\_email\_preview": <Bounced preview email>, ---\> Deprecte the field and use \`bounce\_message.text\`"bounce\_message":{"message\_id":"", ---\> new field use instead of \`bounce\_reply\_message\_id\`
"html":"", ---\> new field use instead of \`bounce\_reply\_email\`
"text":"" ---\> new field use instead of \`bounce\_reply\_email\_preview\`
"time":"" ---\> new field }"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Sample Response

{"campaign\_status":"COMPLETED","client\_id":null,"stats\_id":"id","from\_email":"test@get-smartlead.com","to\_email":"support@test.com","to\_name":"Support Test","time\_sent":"2023-04-04T08:31:13.638+00:00","event\_timestamp":"2023-04-04T08:31:13.638+00:00","campaign\_name":"Link insertion","campaign\_id":111,"sequence\_number":1,"custom\_subject":"Proposal for Collaboration - smartlead.ai","custom\_email\_message":"<div>Hey there</div>","sent\_message\_body":"<div>Hey there</div>","sent\_message":{"message\_id":"<sw-id@get-smartlead.com>","html":"<div>Hey there</div>","text":"Hey there","time":"2023-04-04T08:31:13.638+00:00"},"subject":"Proposal for Collaboration - smartlead.ai","message\_id":"<sw-id@get-smartlead.com>","is\_bounced":true,"bounce\_reply\_message\_id":"<id0\_sprut@zendesk.com>","bounce\_reply\_email":"<p>##- Please type your reply above this line -##</p></p>","bounce\_reply\_email\_preview":"##\- Please type your reply above this line -##","bounce\_message":{"message\_id":"<id0\_sprut@zendesk.com>","html":"<p>##- Please type your reply above this line -##</p></p>","text":"##\- Please type your reply above this line -##","time":"2023-04-04T08:31:22.000Z"},"secret\_key":"secret key","app\_url":"https://app.smartlead.ai/app/master-inbox","ui\_master\_inbox\_link":"https://app.smartlead.ai/app/master-inbox","description":"Email 1 sent to support@test.com got bounced for campaign - Link insertion","metadata":{"webhook\_created\_at":"2023-09-26T10:48:56.598Z"},"webhook\_url":"https://webhook.site/5168faaa-0f49-465a-8111-1522da474abc","webhook\_id":111,"webhook\_name":"Test","event\_type":"EMAIL\_BOUNCE"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

stats\_id: id of the event

event\_type: type of the event

created\_at: the date and time that the webhook was created

time\_replied: Deprecate it and use

event\_timestamp

event\_timestamp: The replied time

from\_email: mailbox used

to\_email: lead email

to\_name: lead name

custom\_subject: Deprecated and use

subject

custom\_email\_message: Deprecated and use

sent\_message.html

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

sent\_message\_body: Deprecate it and instead use

sent\_message.html

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: time email was sent

message\_id: Deprecate it and instead use

sent\_message.message\_id

client\_id: id of client attached to campaign if it belongs to a client

is\_bounced: Deprecate it

bounce\_reply\_message\_id: Deprecate it and instead use

bounce\_message.message\_id

bounce\_reply\_email: Deprecate it and instead use

bounce\_message.html

bounce\_reply\_email\_preview: Deprecate it and instead use

sbounce\_message.text

bounce\_message

message\_id: Bounced message ID

html: Bounced full email

text: Bounced preview email

time: Bounce Message time

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Manual Step Reached

**URL:** https://help.smartlead.ai/Manual-Step-Reached-99aa4a20e2e247c3865f53f11c1a4b20


[Skip to content](https://help.smartlead.ai/Manual-Step-Reached-99aa4a20e2e247c3865f53f11c1a4b20#main)

# Manual Step Reached

Response Structure

{"lead\_name":"","lead\_id":"","lead\_email":"","sent\_message\_ids":\[""\],"campaign\_status":"","campaign\_name":"","client\_id":null,"campaign\_id":111,"current\_sequence\_number":1,"secret\_key":"","app\_url":"","description":"","metadata":{"webhook\_created\_at":""},"webhook\_url":"","webhook\_id":11,"webhook\_name":"","event\_type":""}

​

Example Response

{"lead\_name":"sukhvir 02 \\n Kaur","lead\_id":"138084","lead\_email":"sukhvir.kau@batchservice.com","sent\_message\_ids":\["<sw-96978509-b8f6-4be0-93dd-c56a5ec34fab@smartlead.ai>"\],"campaign\_status":"ACTIVE","campaign\_name":"test56778","client\_id":null,"campaign\_id":353,"current\_sequence\_number":1,"secret\_key":"e0207d40-84ef-4ad6-89eb-7dbff8c0138d","app\_url":"https://app.smartlead.ai/app/email-campaign/353/lead-list","description":"Manual step reached for Campaign - test56778 and lead email - sukhvir.kau@batchservice.com","metadata":{"webhook\_created\_at":"2024-04-12T13:51:26.269Z"},"webhook\_url":"https://webhook.site/05076ec5-99ab-4277-b223-293df0b402e9","webhook\_id":94,"webhook\_name":"test","event\_type":"MANUAL\_STEP\_REACHED"}

​

lead\_name: Name of the lead

lead\_id: ID of the lead

lead\_email: Email of the lead

sent\_message\_ids: Array of all the sent message IDs

webhook\_id : A unique integer identifier for the web hook

campaign\_status: Campaign Status

campaign\_name: Campaign name

client\_id: ID of client campaign belongs to

campaign\_id: ID of campaign

current\_sequence\_number: The sequence number this lead is on for the campaign

secret\_key: Your security key to verify requests

app\_url: Url of campaign

description: Full description of event

webhook\_created\_at: When this webhook was created

webhook\_url: Endpoint for the webhook

webhook\_id: Smartlead allocated webhook ID

webhook\_name: Name given to webhook

event\_type: Name of event occurred


---


## Email Sent

**URL:** https://help.smartlead.ai/Email-Sent-d178e38d71a24e24a92383b7222d46c2


[Skip to content](https://help.smartlead.ai/Email-Sent-d178e38d71a24e24a92383b7222d46c2#main)

# Email Sent

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"sl\_email\_lead\_id":"", ---\> new\_feild
"sl\_email\_lead\_map\_id":"", ---\> new\_feild
"webhook\_url":"","stats\_id":"","event\_type":"EMAIL\_SENT","time\_sent":"", ---\> Deprecate and instead use \`event\_timestamp\`"event\_timestamp":"", ---\> new field use instead of \`time\_sent\`"from\_email":"","to\_email":"","to\_name":"","subject":"","campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"sequence\_number":"","custom\_subject":"", --\> Deprecated instead use \`subject\`
"custom\_email\_message":"", --\> Deprecated instead use \`sent\_message.html\`"sent\_message\_body":"", ---\> Deprecate and instead use \`sent\_message.html\`"sent\_message":{"message\_id":"", ---\> new field for replacing \`message\_id\`"html":"", ---\> new field use instead of \`sent\_message\_body\`
"text":"" ---\> new field
"time":"" ---\> new field }"message\_id":"", ---\> Deprecate and instead use \`sent\_message.message\_id\`"client\_id":"", ---\> new field"app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"campaign\_status":"COMPLETED","client\_id":111,"stats\_id":"id","from\_email":"sample@test.com","to\_email":"test@gmail.com","to\_name":"David Carroll","time\_sent":"2023-09-25T17:27:27.234+00:00","event\_timestamp":"2023-09-25T17:27:27.234+00:00","campaign\_name":"OR Tracker","campaign\_id":111,"sequence\_number":1,"custom\_subject":"OR","custom\_email\_message":"<div>Opening</div>","sent\_message\_body":"<div>Opening</div>","sent\_message":{"message\_id":"<sw-id@test.com>","html":"<div>Opening</div>","text":"Opening","time":"2023-09-25T17:27:27.234+00:00"},"subject":"OR","message\_id":"<sw-id@test.com>","secret\_key":"secret key","app\_url":"https://app.smartlead.ai/app/master-inbox","ui\_master\_inbox\_link":"https://app.smartlead.ai/app/master-inbox","description":"Email 1 sent to test@gmail.com for campaign - OR Tracker","metadata":{"webhook\_created\_at":"2023-09-26T10:19:49.535Z"},"webhook\_url":"https://webhook.site/5168fasf-0sss-465a-8114-1111da474a77","webhook\_id":111,"webhook\_name":"Testing new webhooks","event\_type":"EMAIL\_SENT"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

stats\_id: id of the event

event\_type: type of the event

time\_sent: Deprecate it and use

event\_timestamp

event\_timestamp: time email was sent

from\_email: mailbox used

to\_email: lead email

to\_name: lead name

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

custom\_subject: Deprecated

custom\_email\_message: Deprecated

sent\_message\_body: Deprecate it and instead use

sent\_message.html

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: time email was sent

message\_id: Deprecate it and instead use

sent\_message.id

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Email Replied

**URL:** https://help.smartlead.ai/Email-Replied-aeebacc09db9456fbf23dcf5c6cbd0fd


[Skip to content](https://help.smartlead.ai/Email-Replied-aeebacc09db9456fbf23dcf5c6cbd0fd#main)

# Email Replied

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"sl\_email\_lead\_id":"", ---\> new\_feild // lead id"sl\_email\_lead\_map\_id":"", ---\> new\_feild // gives access to all the chats connected to the lead"sl\_lead\_email":"", ---\> new\_feild //original email address"webhook\_url":"","stats\_id":"","event\_type":"EMAIL\_REPLY","time\_replied":"", ---\> Deprecate and instead use \`event\_timestamp\`"event\_timestamp":"", ---\> new field use instead of \`time\_replied\`"from\_email":"",// is the sender mailbox"to\_email":"",// is the lead that replies OR alias"to\_name":"","subject":"","campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"sequence\_number":"","sent\_message\_body":"",---\> Deprecate and instead use \`sent\_message.html\`"sent\_message":{"message\_id":"", ---\> new field for replacing \`message\_id\`"html":"", ---\> new field use instead of \`sent\_message\_body\`
"text":"" ---\> new field
"time":"" ---\> new field}"message\_id":"", ---\> Deprecate and instead use \`reply\_message.message\_id\`"reply\_body":"", ---\> Deprecate and instead use \`reply\_message.html\`"reply\_message":{"message\_id":"", ---\> new field use instead of \`message\_id\`"html":"", ---\> new field use instead of \`reply\_body\`
"text":"" ---\> new field use instead of \`preview\_text\`
"time":"" ---\> new field},"reply\_category":"","preview\_text":"", ---\> Deprecate and instead use \`reply\_message.text\`"client\_id":"","app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"webhook\_id":100,"webhook\_name":"Test","campaign\_status":"COMPLETED","stats\_id":"id","from\_email":"test@get-smartlead.com","subject":"Proposal for Collaboration - smartlead.ai","sent\_message\_body":"<div>Test</div>","sent\_message":{"message\_id":"<sw-id@get-smartlead.com>","html":"<div>Test</div>","text":"Test","time":"2023-04-04T08:31:13.638+00:00"},"to\_email":"support@test.com","to\_name":"Support Test","time\_replied":"2023-04-04T08:31:22+00:00","event\_timestamp":"2023-04-04T08:31:22+00:00","reply\_message":{"message\_id":"<id@zendesk.com>","html":"<p>##- Please type your reply above this line -##</p>","text":"##\- Please type your reply above this line -##","time":"2023-04-04T08:31:22+00:00"},"reply\_body":"<p>##- Please type your reply above this line -##</p>","message\_id":"<id@zendesk.com>","preview\_text":"##\- Please type your reply above this line -##","campaign\_name":"Link insertion","campaign\_id":100,"client\_id":null,"sequence\_number":1,"secret\_key":"secretkey","app\_url":"https://app.smartlead.ai/app","ui\_master\_inbox\_link":"https://app.smartlead.ai/app","description":"support@test.com replied to Email 1 for campaign - Link insertion ","metadata":{"webhook\_created\_at":"2023-09-26T10:48:56.598Z"},"webhook\_url":"https://webhook.site/5168fa7f-0asd-465a-8114-111da474a77","event\_type":"EMAIL\_REPLY"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

stats\_id: id of the event

event\_type: type of the event

time\_replied: Deprecate it and use

event\_timestamp

event\_timestamp: The replied time

from\_email: mailbox used

to\_email: lead email

to\_name: lead name

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

sent\_message\_body: Deprecate it and instead use

sent\_message.html

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: sent message time

message\_id: Deprecate it and instead use

reply\_message.id

reply\_body: Deprecate and instead use

reply\_message.html

preview\_text: Deprecate and instead use

reply\_message.text

reply\_message:

message\_id: unique id of the message replied

html: copy of the reply from the lead in full copy (html if there is)

text: copy of the latest reply in plain text

time: The replied time

reply\_category

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Lead Unsubscribed

**URL:** https://help.smartlead.ai/Lead-Unsubscribed-5b21eed0deac40fc84190b46d963ce4e


[Skip to content](https://help.smartlead.ai/Lead-Unsubscribed-5b21eed0deac40fc84190b46d963ce4e#main)

# Lead Unsubscribed

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"webhook\_url":"","event\_type":"LEAD\_UNSUBSCRIBED","event\_timestamp":"", ---\> new field"from\_email":"", ---\> new field (optional)"to\_email":"", ---\> new field use instead of \`lead\_email\`
"lead\_email":"", ---\> Deprecate and instead use \`to\_email\`
"lead\_name":"", ---\> Deprecate and instead use \`to\_name\`"to\_name":"", ---\> new field use instead of \`lead\_name\`
"subject":"", ---\> new field (optional)"campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field (optional)
"sequence\_number":"", ---\> new field (optional)
"unsubscribed\_client\_id\_map":"","sent\_message":{"message\_id":"", ---\> new field
"html":"", ---\> new field
"text":"" ---\> new field
"time":"" ---\> new field
}, (optional)"client\_id":"" ---\> new field (optional)"app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"event\_timestamp":"2023-09-26T11:16:24.671Z","lead\_email":"test@gmail.com","to\_email":"test@gmail.com","from\_email":"test@five2one.com.au","lead\_name":"Bob","to\_name":"Bob","sequence\_number":1,"sent\_message":{"message\_id":"<id@five2one.com.au>","html":"<div>Testing email </div>","text":"Testing email","time":"2023-08-25T08:28:06.619Z"},"campaign\_id":101,"unsubscribed\_client\_id\_map":{},"secret\_key":"secretkey","app\_url":"https://app.smartlead.ai/app/master-inbox","ui\_master\_inbox\_link":"https://app.smartlead.ai/app/master-inbox","description":"Lead - test@gmail.com unsubscribed from the campaign","metadata":{"webhook\_created\_at":"2023-09-26T11:02:01.385Z"},"webhook\_url":"https://webhook.site/5168faaa-0f49-465a-8111-1522da474abc","webhook\_id":101,"webhook\_name":"Test","event\_type":"LEAD\_UNSUBSCRIBED"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

event\_type: type of the event

event\_timestamp: The replied time

from\_email: mailbox used

to\_email: lead email

lead\_email:Deprecate and instead use \`to\_email\`

to\_name: lead name

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

unsubscribed\_client\_id\_map:

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: time email was sent

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Threaded Replies

**URL:** https://help.smartlead.ai/Threaded-Replies-ff92a607c93645b7b1568d8219218423


[Skip to content](https://help.smartlead.ai/Threaded-Replies-ff92a607c93645b7b1568d8219218423#main)

# Threaded Replies

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"sl\_email\_lead\_id":"", ---\> new\_feild // lead id"sl\_email\_lead\_map\_id":"", ---\> new\_feild // gives access to all the chats connected to the lead"sl\_lead\_email":"", ---\> new\_feild //original email address"webhook\_url":"","stats\_id":"","stats\_thread\_id":"","event\_type":"EMAIL\_REPLY","time\_replied":"", ---\> Deprecate and instead use \`event\_timestamp\`"event\_timestamp":"", ---\> new field use instead of \`time\_replied\`"from\_email":"",// is the sender mailbox"to\_email":"","to\_name":"",// is the lead that replies OR alias"subject":"","campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"sequence\_number":"","sent\_message\_body":"", ---\> Deprecate and instead use \`sent\_message.html\`"sent\_message":{"message\_id":"", ---\> new field"html":"", ---\> new field use instead of \`sent\_message\_body\`
"text":"" ---\> new field
"time":"" ---\> new field}"message\_id":"", ---\> Deprecate and instead use \`reply\_message.message\_id\`"reply\_body":"", ---\> Deprecate and instead use \`reply\_message.html\`"reply\_message":{"message\_id":"", ---\> new field use instead of \`message\_id\`
"html":"", ---\> new field use instead of \`reply\_body\`
"text":"" ---\> new field use instead of \`preview\_text\`
"time":"" ---\> new field},"preview\_text":"", ---\> Deprecate and instead use \`reply\_message.text\`"client\_id":"","app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"webhook\_id":100,"webhook\_name":"Test","campaign\_status":"COMPLETED","stats\_id":"id","stats\_thread\_id":"thread\_id","from\_email":"test@get-smartlead.com","subject":"Proposal for Collaboration - smartlead.ai","sent\_message\_body":"<div>Test</div>","sent\_message":{"message\_id":"<sw-id@get-smartlead.com>","html":"<div>Test</div>","text":"Test","time":"2023-04-04T08:31:13.638+00:00"},"to\_email":"support@test.com","to\_name":"Support Test","time\_replied":"2023-04-04T08:31:22+00:00","event\_timestamp":"2023-04-04T08:31:22+00:00","reply\_message":{"message\_id":"<id@zendesk.com>","html":"<p>##- Please type your reply above this line -##</p>","text":"##\- Please type your reply above this line -##","time":"2023-04-04T08:31:22+00:00"},"reply\_body":"<p>##- Please type your reply above this line -##</p>","message\_id":"<id@zendesk.com>","preview\_text":"##\- Please type your reply above this line -##","campaign\_name":"Link insertion","campaign\_id":100,"client\_id":null,"sequence\_number":1,"secret\_key":"secretkey","app\_url":"https://app.smartlead.ai/app","ui\_master\_inbox\_link":"https://app.smartlead.ai/app","description":"support@test.com replied to Email 1 for campaign - Link insertion ","metadata":{"webhook\_created\_at":"2023-09-26T10:48:56.598Z"},"webhook\_url":"https://webhook.site/5168fa7f-0asd-465a-8114-111da474a77","event\_type":"EMAIL\_REPLY"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

stats\_id: id of the event

stats\_thread\_id: Identify it is a thread,

event\_type: type of the event

time\_replied: Deprecate it and use

event\_timestamp

event\_timestamp: The replied time

from\_email: mailbox used

to\_email: lead email

to\_name: lead name

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

sent\_message\_body: Deprecate it and instead use

sent\_message.html

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: sent time

message\_id: Deprecate it and instead use

reply\_message.id

reply\_body: Deprecate and instead use

reply\_message.html

preview\_text: Deprecate and instead use

reply\_message.text

reply\_message:

message\_id: unique id of the message replied

html: copy of the reply from the lead in full copy (html if there is)

text: copy of the latest reply in plain text

time: reply time

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Email Opened

**URL:** https://help.smartlead.ai/Email-Opened-466fc579d2d942a688d52ec51b6e0ae6


[Skip to content](https://help.smartlead.ai/Email-Opened-466fc579d2d942a688d52ec51b6e0ae6#main)

# Email Opened

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"sl\_email\_lead\_id":"", ---\> new\_feild
"sl\_email\_lead\_map\_id":"", ---\> new\_feild
"webhook\_url":"","stats\_id":"","event\_type":"EMAIL\_OPEN","time\_opened":"", ---\> Deprecate and instead use \`event\_timestamp\`"event\_timestamp":"", ---\> new field use instead of \`time\_replied\`"from\_email":"","to\_email":"","to\_name":"","subject":"","campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"sequence\_number":"","sent\_message\_body":"",---\> Deprecate and instead use \`sent\_message.html\`"sent\_message":{"message\_id":"", ---\> new field"html":"", ---\> new field use instead of \`sent\_message\_body\`
"text":"" ---\> new field
"time":"" ---\> new field },"client\_id":"" ---\> new field"app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"campaign\_status":"COMPLETED","client\_id":111,"stats\_id":"id","from\_email":"test@test.com","to\_email":"test@test.com","to\_name":"David Carroll","time\_opened":"2023-09-25T17:29:11.618881+00:00","event\_timestamp":"2023-09-25T17:29:11.618881+00:00","campaign\_name":"OR Tracker","campaign\_id":111,"sequence\_number":1,"subject":"OR","sent\_message\_body":"<div>Opening</div>","sent\_message":{"message\_id":"<sw-id@test.com>","html":"<div>Opening</div>","text":"Opening"},"secret\_key":"secret key","app\_url":"https://app.smartlead.ai/app/master-inbox","ui\_master\_inbox\_link":"https://app.smartlead.ai/app/master-inbox","description":"test@test.com opened Email 1 for campaign - OR Tracker","metadata":{"webhook\_created\_at":"2023-09-26T10:19:49.535Z"},"webhook\_url":"https://webhook.site/5168faa-0f49-4111-8114-1123da474b77","webhook\_id":111,"webhook\_name":"Testing new webhooks","event\_type":"EMAIL\_OPEN"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

stats\_id: id of the event

event\_type: type of the event

time\_opened: Deprecate it and use

event\_timestamp

event\_timestamp: The replied time

from\_email: mailbox used

to\_email: lead email

to\_name: lead name

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

sent\_message\_body: Deprecate it and instead use

sent\_message.html

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: time email was sent

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Link Clicked

**URL:** https://help.smartlead.ai/Link-Clicked-afd2fb5f11164db986bf5cef251825de


[Skip to content](https://help.smartlead.ai/Link-Clicked-afd2fb5f11164db986bf5cef251825de#main)

# Link Clicked

Response Structure

{"webhook\_id":"", ---\> new\_feild"webhook\_name":"", ---\> new\_feild
"sl\_email\_lead\_id":"", ---\> new\_feild
"sl\_email\_lead\_map\_id":"", ---\> new\_feild
"webhook\_url":"","stats\_id":"","event\_type":"EMAIL\_LINK\_CLICK","time\_clicked":"", ---\> Deprecate and instead use \`event\_timestamp\`"event\_timestamp":"", ---\> new field use instead of \`time\_clicked\`
"link\_clicked":"", ---\> Deprecate and instead use \`link\_details\`"link\_details":"", ---\> new field use instead of \`link\_clicked\`"from\_email":"","to\_email":"","to\_name":"","subject":"","campaign\_id":"","campaign\_name":"","campaign\_status":"", ---\> new field
"sequence\_number":"","sent\_message\_body":"",---\> Deprecate and instead use \`sent\_message.html\`"sent\_message":{"id":"", ---\> new field"html":"", ---\> new field use instead of \`sent\_message\_body\`
"text":"" ---\> new fiel
"time":"" ---\> new field }"client\_id":"", ---\> new field"app\_url":"", ---\> new field use instead of \`ui\_master\_inbox\_link\`"ui\_master\_inbox\_link":"", ---\> Deprecate and instead use \`app\_url\`"secret\_key":"","description":"", ---\> new field
"metadata":{"webhook\_created\_at":"", ---\> new field
} ---\> new field}

​

Example Response

{"campaign\_status":"COMPLETED","client\_id":111,"stats\_id":"id","from\_email":"test@test.com","to\_email":"test@gmail.com","to\_name":"Bob","time\_clicked":"2023-09-25T17:30:11.618881+00:00","event\_timestamp":"2023-09-25T17:30:11.618881+00:00","link\_clicked":\["www.google.com"\],"link\_details":\["www.google.com"\],"campaign\_name":"OR Tracker","campaign\_id":111,"sequence\_number":1,"subject":"OR","sent\_message\_body":"<div>Opening</div>","sent\_message":{"message\_id":"<sw-id@test.com>","html":"<div>Opening</div>","text":"Opening","time":"2023-09-25T17:30:11.618881+00:00"},"secret\_key":"secret key","app\_url":"https://app.smartlead.ai/app/master-inbox","ui\_master\_inbox\_link":"https://app.smartlead.ai/app/master-inbox","description":"test@gmail.com clicked on a link in Email 1 for campaign - OR Tracker","metadata":{"webhook\_created\_at":"2023-09-26T10:19:49.535Z"},"webhook\_url":"https://webhook.site/5168faaa-0f49-434a-8114-1522da474asd","webhook\_id":123,"webhook\_name":"Testing new webhooks","event\_type":"EMAIL\_LINK\_CLICK"}

​

webhook\_id : A unique integer identifier for the web hook

webhook\_name: Name of the web hook

webhook\_url: The URL that the event data will be posted to

stats\_id: id of the event

event\_type: type of the event

time\_replied: Deprecate it and use

event\_timestamp

event\_timestamp: The replied time

link\_clicked: Deprecate and instead use

link\_url

link\_details: details of the clicked link

from\_email: mailbox used

to\_email: lead email

to\_name: lead name

subject: subject of the message sent

campaign\_id: campaign id for your personal identification

campaign\_name: name of the campaign this event belongs to

campaign\_status: Status of the campaign

sequence\_number: the sequence number that triggered this event

sent\_message\_body: Deprecate it and instead use

sent\_message.html

sent\_message:

message\_id: unique id of that exact message sent

html: Body of the message sent full copy (html if there is)

text: copy of the message in plain text

time: time email was sent

client\_id: id of client attached to campaign if it belongs to a client

app\_url: link to actual reply

ui\_master\_inbox\_link: deprecate it and instead use

app\_url

secret\_key: the secret to identify the webhook is from smartlead

description: An optional description of what the webhook is used for.

metadata :Set of [key-value pairs](https://stripe.com/docs/api/metadata) that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

webhook\_created\_at: the date and time that the webhook was created

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Campaign Status Change

**URL:** https://help.smartlead.ai/Campaign-Status-Change-6c6fe98602b346aebdaf7c2ff9bae7e7


[Skip to content](https://help.smartlead.ai/Campaign-Status-Change-6c6fe98602b346aebdaf7c2ff9bae7e7#main)

# Campaign Status Change

Response Structure

{"previous\_status":"","current\_status":"","campaign\_status":"","client\_id":null,"campaign\_name":"","campaign\_id":000,"secret\_key":"e0207d40-84ef-4ad6-89eb-7dbff8c0138d","app\_url":"","description": ","metadata":{"webhook\_created\_at":""},"webhook\_url":"","webhook\_id":11,"webhook\_name":"","event\_type":""}

​

Example Response

{"previous\_status":"PAUSED","current\_status":"ACTIVE","campaign\_status":"ACTIVE","client\_id":null,"campaign\_name":"377 testing manual step","campaign\_id":377,"secret\_key":"e0207d40-84ef-4ad6-89eb-7dbff8c0138d","app\_url":"https://app.smartlead.ai/app/app/email-campaign/377/analytics","description":"Email Campaign status changed PAUSED to ACTIVE for campaign - 377 testing manual step","metadata":{"webhook\_created\_at":"2024-04-12T13:51:26.269Z"},"webhook\_url":"https://webhook.site/05076ec5-99ab-4277-b223-293df0b402e9","webhook\_id":94,"webhook\_name":"test","event\_type":"CAMPAIGN\_STATUS\_CHANGED"}

​

webhook\_id : A unique integer identifier for the web hook

previous\_status: Original status of the campaign

current\_status: Current campaign Status

campaign\_status: Campaign Status

client\_id: ID of client campaign belongs to

campaign\_name: Campaign name

campaign\_id: ID of campaign

secret\_key: Your security key to verify requests

app\_url: Url of campaign

description: Full description of event

webhook\_created\_at: When this webhook was created

webhook\_url: Endpoint for the webhook

webhook\_id: Smartlead allocated webhook ID

webhook\_name: Name given to webhook

event\_type: Name of event occurred

Note:

New fields are in green colour

Existing fields are in black,

Fields that are deprecated are in purple

Fields will be deprecate are in red

Fields that are replacing the deprecated fields are in blue colour.


---


## Beta Agency View

**URL:** https://help.smartlead.ai/Beta-Agency-View-1a5b6f441f9f418dbb58bdbf665499d7


[Skip to content](https://help.smartlead.ai/Beta-Agency-View-1a5b6f441f9f418dbb58bdbf665499d7#main)

![🌅 Page icon](<Base64-Image-Removed>)![🌅 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f305.svg)

# Beta Agency View

Date

July 4, 2022

Assign

Empty

Status

Completed


---


## Subsequences

**URL:** https://help.smartlead.ai/Subsequences-ff786640813e4acdae2442637be5f746


[Skip to content](https://help.smartlead.ai/Subsequences-ff786640813e4acdae2442637be5f746#main)

![💰 Page icon](<Base64-Image-Removed>)![💰 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f4b0.svg)

# Subsequences

Date

September 5, 2022 → September 12, 2022

Assign

Empty

Status

Completed


---


## Multiple Seats

**URL:** https://help.smartlead.ai/Multiple-Seats-7a729099c4d747d395955e7792b46aaf


[Skip to content](https://help.smartlead.ai/Multiple-Seats-7a729099c4d747d395955e7792b46aaf#main)

![💺 Page icon](<Base64-Image-Removed>)![💺 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f4ba.svg)

# Multiple Seats

Date

November 7, 2022 → November 10, 2022

Assign

Empty

Status

Completed


---


## Native CRM Integrations

**URL:** https://help.smartlead.ai/Native-CRM-Integrations-8ba12fd57f1942a3871285164eb32428


[Skip to content](https://help.smartlead.ai/Native-CRM-Integrations-8ba12fd57f1942a3871285164eb32428#main)

![🏏 Page icon](<Base64-Image-Removed>)![🏏 Page icon](https://notion-emojis.s3-us-west-2.amazonaws.com/prod/svg-twitter/1f3cf.svg)

# Native CRM Integrations

Date

March 7, 2023 → April 4, 2023

Assign

Empty

Status

Empty

Salesforce

Hubsport

Pipedrive

And more


---


## Why am I getting a ‘Connection Timed Out’ error?

**URL:** https://help.smartlead.ai/Why-am-I-getting-a-Connection-Timed-Out-error-bbe68c07d5e64d2582a31780f708bd02


[Skip to content](https://help.smartlead.ai/Why-am-I-getting-a-Connection-Timed-Out-error-bbe68c07d5e64d2582a31780f708bd02#main)

# Why am I getting a ‘Connection Timed Out’ error?

If you get a ‘Connection Timed out’ error when connecting, it means that you are using an smtp port that is blocked, in this case per settings would be 465. By default, we recommend using port 465 when sending emails.

However, some ISPs may block port 465. If this is the case, try using port 587 in the SMTP section instead.


---


##  Test Email Before Sending

**URL:** https://help.smartlead.ai/Test-Email-Before-Sending-05c56e7280294d55b8858834713029a7


[Skip to content](https://help.smartlead.ai/Test-Email-Before-Sending-05c56e7280294d55b8858834713029a7#main)

# ![👀](<Base64-Image-Removed>) Test Email Before Sending

Date

June 13, 2022

Assign

Empty

Status

Completed


---

