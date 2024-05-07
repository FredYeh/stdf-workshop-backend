const createError = require('http-errors')
const express = require('express')
const path = require('path')
const cookieParser = require('cookie-parser')
const logger = require('morgan')
// const cookieSession = require('cookie-session')
const stdfRouter = require('./routes/stdf')
const mongoose = require('./utils/dbTool/db')
mongoose()

const { dateFormat } = require('./utils/format/date')

const app = express()
//Websocket
var expressWs = require('express-ws')(app)
// view engine setup
app.set('views', path.join(__dirname, 'views'))
app.set('view engine', 'ejs')

app.use(logger('dev'))
app.use(express.json())
app.use(express.urlencoded({ extended: false }))
app.use(cookieParser())
app.use(express.static(path.join(__dirname, 'public')))

const wsClients = {}
app.wsClients = wsClients

app.ws('/websocket/:id', function (ws, req) {
  const { id } = req.params
  ws.id = id
  wsClients[ws.id] = ws

  console.log('connect success', id)
  ws.send(
    JSON.stringify({
      code: 200,
      target: 'default',
      msg: 'connect to express server with WebSocket success'
    })
  )
  ws.on('message', function (msg) {
    console.log(`receive message ${msg}`)
    ws.send(
      JSON.stringify({
        code: 200,
        target: 'default',
        msg: 'default response'
      })
    )
  })

  // close 事件表示客户端断开连接时执行的回调函数
  ws.on('close', function (e) {
    delete wsClients[ws.id]
    console.log('connect close', wsClients)
  })
})
app.use('/stdf', stdfRouter)

// catch 404 and forward to error handler
app.use(function (req, res, next) {
  next(createError(404))
})

// error handler
app.use(function (err, req, res, next) {
  // set locals, only providing error in development
  // res.locals.message = err.message
  // res.locals.error = req.app.get('env') === 'development' ? err : {}

  // render the error page
  // res.status(err.status || 500)
  res.render('error', {
    msg: err.message,
    data: JSON.stringify({
      date: dateFormat()
    })
  })
})

module.exports = app
