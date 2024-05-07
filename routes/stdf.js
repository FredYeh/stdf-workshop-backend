const express = require('express')
const router = express.Router()

const { handleVerify, handleFormData, handleMerge, handleDownload } = require('../controllers/upload')
const { handleGetServiceCount } = require('../controllers/queryDB')
const {
  handleParse,
  handleRecipe,
  handleCompare,
  handleRepair,
  handleFolder,
  handleHeader,
  handleEditor,
  handleTextToExcel,
  handleToCsv,
  handleReadDat,
  handleRmReading,
  handleMergeSTDFs
} = require('../controllers/services')

router.post('/verify', handleVerify)
router.post('/upload', handleFormData)
router.post('/merge', handleMerge)
router.post('/getServiceCount/', handleGetServiceCount)
router.post('/parser/:socketId', handleParse)
router.post('/recipeBuyoff/:socketId', handleRecipe)
router.post('/stdfCompare/:socketId', handleCompare)
router.post('/stdfRepair/:socketId', handleRepair)
router.post('/parseFolder/:socketId', handleFolder)
router.post('/stdfHeader/:socketId', handleHeader)
router.post('/stdfEditor/:socketId', handleEditor)
router.post('/textToExcel/:socketId', handleTextToExcel)
router.post('/stdfToCsv/:socketId', handleToCsv)
router.post('/readDat/:socketId', handleReadDat)
router.post('/rmReading/:socketId', handleRmReading)
router.post('/mergeSTDFs/:socketId', handleMergeSTDFs)
router.post('/download/:filename', handleDownload)

module.exports = router
